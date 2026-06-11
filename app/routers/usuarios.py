import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Usuario, UsuarioTarea, Tarea
from app.schemas.schemas import UsuarioCreate, UsuarioUpdate, UsuarioOut, CambiarContrasenaRequest
from app.utils.security import hashear_contrasena, verificar_contrasena, verificar_token
from fastapi.security import OAuth2PasswordBearer
from typing import List

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    usuario = db.query(Usuario).filter(Usuario.idUsuario == int(payload["sub"])).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario

def solo_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rolUsuario != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos para realizar esta acción")
    return current_user


@router.post("/cambiar-contrasena")
def cambiar_contrasena(
    datos: CambiarContrasenaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not verificar_contrasena(datos.contrasena_actual, current_user.contraseñaUsuario):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

    current_user.contraseñaUsuario = hashear_contrasena(datos.nueva_contrasena)
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}


@router.get("/", response_model=List[UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    return db.query(Usuario).all()


@router.get("/{idUsuario}", response_model=UsuarioOut)
def obtener_usuario(idUsuario: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rolUsuario != "admin" and current_user.idUsuario != idUsuario:
        raise HTTPException(status_code=403, detail="No tienes permisos para realizar esta acción")

    usuario = db.query(Usuario).filter(Usuario.idUsuario == idUsuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.post("/", response_model=UsuarioOut)
def crear_usuario(usuario_data: UsuarioCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    existe = db.query(Usuario).filter(Usuario.emailUsuario == usuario_data.emailUsuario).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese correo")
    
    nuevo_usuario = Usuario(
        nombreUsuario=usuario_data.nombreUsuario,
        apellidosUsuario=usuario_data.apellidosUsuario,
        emailUsuario=usuario_data.emailUsuario,
        contraseñaUsuario=hashear_contrasena(usuario_data.contraseñaUsuario),
        rolUsuario=usuario_data.rolUsuario,
        fotoUsuario=usuario_data.fotoUsuario
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.put("/{idUsuario}", response_model=UsuarioOut)
def actualizar_usuario(idUsuario: int, usuario_data: UsuarioUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    usuario = db.query(Usuario).filter(Usuario.idUsuario == idUsuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user.rolUsuario != "admin" and current_user.idUsuario != idUsuario:
        raise HTTPException(status_code=403, detail="No tienes permisos para realizar esta acción")
    
    if usuario_data.nombreUsuario is not None:
        usuario.nombreUsuario = usuario_data.nombreUsuario
    if usuario_data.apellidosUsuario is not None:
        usuario.apellidosUsuario = usuario_data.apellidosUsuario
    if usuario_data.fotoUsuario is not None:
        usuario.fotoUsuario = usuario_data.fotoUsuario
    
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/{idUsuario}/foto")
def subir_foto_usuario(
    idUsuario: int,
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    usuario = db.query(Usuario).filter(Usuario.idUsuario == idUsuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if current_user.rolUsuario != "admin" and current_user.idUsuario != idUsuario:
        raise HTTPException(status_code=403, detail="No tienes permisos para realizar esta acción")

    if not foto.content_type or not foto.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    extensiones = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    extension = extensiones.get(foto.content_type, foto.content_type.split("/")[-1])

    nombre_archivo = f"usuario_{idUsuario}.{extension}"
    ruta = os.path.join("static", "fotos", nombre_archivo)
    with open(ruta, "wb") as f:
        f.write(foto.file.read())

    base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    url_completa = f"{base_url}/static/fotos/{nombre_archivo}"
    usuario.fotoUsuario = url_completa
    db.commit()
    db.refresh(usuario)

    return {"fotoUsuario": url_completa}


@router.delete("/{idUsuario}")
def eliminar_usuario(idUsuario: int, reasignar_a: int = None, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    usuario = db.query(Usuario).filter(Usuario.idUsuario == idUsuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user.idUsuario == idUsuario:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    
    # Reasignar tareas creadas por este usuario
    if reasignar_a:
        nuevo_responsable = db.query(Usuario).filter(Usuario.idUsuario == reasignar_a).first()
        if not nuevo_responsable:
            raise HTTPException(status_code=404, detail="El usuario al que reasignar no existe")
        db.query(Tarea).filter(Tarea.idUsuarioFK == idUsuario).update({"idUsuarioFK": reasignar_a})
    
    # Eliminar asignaciones de tareas
    db.query(UsuarioTarea).filter(UsuarioTarea.idUsuarioFK == idUsuario).delete()
    
    db.delete(usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado correctamente"}