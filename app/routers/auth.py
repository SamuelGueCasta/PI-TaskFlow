from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Usuario, RecuperacionContrasena
from app.schemas.schemas import LoginRequest, Token, RecuperacionRequest, NuevaContrasenaRequest
from app.utils.security import verificar_contrasena, crear_token, hashear_contrasena
from app.utils.email import enviar_email_recuperacion
from datetime import datetime, timedelta
import secrets
import html

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.emailUsuario == request.emailUsuario).first()
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not verificar_contrasena(request.contraseñaUsuario, usuario.contraseñaUsuario):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    token = crear_token({"sub": str(usuario.idUsuario), "rol": usuario.rolUsuario})
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": usuario.rolUsuario,
        "idUsuario": usuario.idUsuario,
    }


@router.post("/recuperar-contrasena")
async def recuperar_contrasena(request: RecuperacionRequest, db: Session = Depends(get_db)):
    # Respuesta genérica: no revelar si el correo existe en el sistema.
    mensaje_generico = {"mensaje": "Si el correo está registrado, se enviará un enlace de recuperación"}

    usuario = db.query(Usuario).filter(Usuario.emailUsuario == request.emailUsuario).first()
    if not usuario:
        return mensaje_generico

    # Eliminar token anterior si existe
    db.query(RecuperacionContrasena).filter(
        RecuperacionContrasena.idUsuarioFK == usuario.idUsuario
    ).delete()

    # Generar nuevo token
    token = secrets.token_urlsafe(32)
    expiracion = datetime.utcnow() + timedelta(hours=1)

    recuperacion = RecuperacionContrasena(
        token=token,
        expiracion=expiracion,
        idUsuarioFK=usuario.idUsuario
    )
    db.add(recuperacion)
    db.commit()

    await enviar_email_recuperacion(usuario.emailUsuario, token)

    return mensaje_generico


@router.post("/resetear-contrasena")
def resetear_contrasena(request: NuevaContrasenaRequest, db: Session = Depends(get_db)):
    recuperacion = db.query(RecuperacionContrasena).filter(
        RecuperacionContrasena.token == request.token
    ).first()
    
    if not recuperacion:
        raise HTTPException(status_code=400, detail="Token inválido")
    
    if datetime.utcnow() > recuperacion.expiracion:
        db.delete(recuperacion)
        db.commit()
        raise HTTPException(status_code=400, detail="El token ha expirado")
    
    usuario = db.query(Usuario).filter(
        Usuario.idUsuario == recuperacion.idUsuarioFK
    ).first()
    
    usuario.contraseñaUsuario = hashear_contrasena(request.nueva_contrasena)
    db.delete(recuperacion)
    db.commit()

    return {"mensaje": "Contraseña actualizada correctamente"}


def _pagina_html(titulo: str, contenido: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo} - TaskFlow</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #EFF6FF;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
        }}
        .card {{
            background: #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(37, 99, 235, 0.1);
            padding: 32px;
            width: 100%;
            max-width: 420px;
        }}
        h1 {{
            color: #2563EB;
            margin: 0 0 8px;
            font-size: 22px;
        }}
        p {{ color: #1E3A8A; margin: 0 0 20px; line-height: 1.5; }}
        label {{
            display: block;
            color: #1E3A8A;
            font-weight: 600;
            margin: 12px 0 6px;
            font-size: 14px;
        }}
        input[type="password"] {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #BFDBFE;
            border-radius: 8px;
            font-size: 15px;
            outline: none;
        }}
        input[type="password"]:focus {{ border-color: #2563EB; }}
        button {{
            margin-top: 20px;
            width: 100%;
            padding: 12px;
            background: #2563EB;
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }}
        button:hover {{ background: #1D4ED8; }}
        .error {{ color: #B91C1C; }}
        .ok {{ color: #15803D; }}
    </style>
</head>
<body>
    <div class="card">
        {contenido}
    </div>
</body>
</html>"""


@router.get("/resetear-contrasena", response_class=HTMLResponse)
def pagina_resetear_contrasena(token: str, db: Session = Depends(get_db)):
    recuperacion = db.query(RecuperacionContrasena).filter(
        RecuperacionContrasena.token == token
    ).first()

    if not recuperacion or datetime.utcnow() > recuperacion.expiracion:
        contenido = """
            <h1 class="error">Enlace no válido</h1>
            <p>El enlace ha expirado o no es válido. Solicita uno nuevo desde la app.</p>
        """
        return HTMLResponse(content=_pagina_html("Enlace no válido", contenido), status_code=400)

    token_seguro = html.escape(token, quote=True)
    contenido = f"""
        <h1>Restablecer contraseña</h1>
        <p>Introduce tu nueva contraseña para completar la recuperación.</p>
        <form method="POST" action="/auth/resetear-contrasena-web" enctype="application/x-www-form-urlencoded">
            <input type="hidden" name="token" value="{token_seguro}">
            <label for="nueva_contrasena">Nueva contraseña</label>
            <input type="password" id="nueva_contrasena" name="nueva_contrasena" required minlength="1">
            <label for="confirmar_contrasena">Confirmar contraseña</label>
            <input type="password" id="confirmar_contrasena" name="confirmar_contrasena" required minlength="1">
            <button type="submit">Guardar contraseña</button>
        </form>
    """
    return HTMLResponse(content=_pagina_html("Restablecer contraseña", contenido))


@router.post("/resetear-contrasena-web", response_class=HTMLResponse)
def resetear_contrasena_form(
    token: str = Form(...),
    nueva_contrasena: str = Form(...),
    confirmar_contrasena: str = Form(...),
    db: Session = Depends(get_db),
):
    if nueva_contrasena != confirmar_contrasena:
        token_seguro = html.escape(token, quote=True)
        contenido = f"""
            <h1 class="error">Las contraseñas no coinciden</h1>
            <p>Vuelve a introducir la nueva contraseña y su confirmación.</p>
            <form method="POST" action="/auth/resetear-contrasena-web" enctype="application/x-www-form-urlencoded">
                <input type="hidden" name="token" value="{token_seguro}">
                <label for="nueva_contrasena">Nueva contraseña</label>
                <input type="password" id="nueva_contrasena" name="nueva_contrasena" required minlength="1">
                <label for="confirmar_contrasena">Confirmar contraseña</label>
                <input type="password" id="confirmar_contrasena" name="confirmar_contrasena" required minlength="1">
                <button type="submit">Guardar contraseña</button>
            </form>
        """
        return HTMLResponse(content=_pagina_html("Las contraseñas no coinciden", contenido), status_code=400)

    recuperacion = db.query(RecuperacionContrasena).filter(
        RecuperacionContrasena.token == token
    ).first()

    if not recuperacion or datetime.utcnow() > recuperacion.expiracion:
        if recuperacion:
            db.delete(recuperacion)
            db.commit()
        contenido = """
            <h1 class="error">Enlace no válido</h1>
            <p>El enlace ha expirado o no es válido. Solicita uno nuevo desde la app.</p>
        """
        return HTMLResponse(content=_pagina_html("Enlace no válido", contenido), status_code=400)

    usuario = db.query(Usuario).filter(
        Usuario.idUsuario == recuperacion.idUsuarioFK
    ).first()

    usuario.contraseñaUsuario = hashear_contrasena(nueva_contrasena)
    db.delete(recuperacion)
    db.commit()

    contenido = """
        <h1 class="ok">Contraseña actualizada</h1>
        <p>Tu contraseña se ha actualizado correctamente. Ya puedes volver a la app e iniciar sesión.</p>
    """
    return HTMLResponse(content=_pagina_html("Contraseña actualizada", contenido))