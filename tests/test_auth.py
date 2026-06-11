"""
Pruebas de caja blanca: autenticacion y tokens JWT.
Codigo bajo prueba: app/routers/auth.py y app/utils/security.py
"""
from conftest import auth_header
from app.utils.security import crear_token, verificar_token


# --- Login con credenciales validas e invalidas (auth.py:15-31) ---

def test_login_credenciales_validas(client, admin_user):
    r = client.post("/auth/login", json={
        "emailUsuario": "admin@taskflow.com",
        "contraseñaUsuario": "admin123",
    })
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["rol"] == "admin"
    assert cuerpo["idUsuario"] == admin_user.idUsuario
    assert cuerpo["access_token"]


def test_login_email_inexistente(client):
    r = client.post("/auth/login", json={
        "emailUsuario": "noexiste@taskflow.com",
        "contraseñaUsuario": "cualquiera123",
    })
    assert r.status_code == 401
    assert r.json()["detail"] == "Credenciales incorrectas"


def test_login_contrasena_incorrecta(client, admin_user):
    r = client.post("/auth/login", json={
        "emailUsuario": "admin@taskflow.com",
        "contraseñaUsuario": "incorrecta123",
    })
    assert r.status_code == 401
    assert r.json()["detail"] == "Credenciales incorrectas"


# --- Generacion y validacion de tokens JWT (security.py:21-32) ---

def test_crear_y_verificar_token():
    token = crear_token({"sub": "1", "rol": "admin"})
    payload = verificar_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["rol"] == "admin"
    assert "exp" in payload


def test_verificar_token_invalido_devuelve_none():
    assert verificar_token("token.manipulado.invalido") is None


# --- Acceso a ruta protegida sin token o con token invalido (usuarios.py:15-22) ---

def test_ruta_protegida_sin_token(client):
    r = client.get("/usuarios/")
    assert r.status_code == 401


def test_ruta_protegida_token_invalido(client):
    r = client.get("/usuarios/", headers=auth_header("token_falso"))
    assert r.status_code == 401
    assert r.json()["detail"] == "Token inválido o expirado"


# --- Recuperacion de contrasena (auth.py:34-87) ---

def test_recuperar_contrasena_email_inexistente_mensaje_generico(client):
    r = client.post("/auth/recuperar-contrasena", json={
        "emailUsuario": "noexiste@taskflow.com",
    })
    assert r.status_code == 200
    assert "recuperación" in r.json()["mensaje"]


def test_resetear_contrasena_token_invalido(client):
    r = client.post("/auth/resetear-contrasena", json={
        "token": "token_inexistente",
        "nueva_contrasena": "nueva123",
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "Token inválido"
