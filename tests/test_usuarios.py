"""
Pruebas de caja blanca: CRUD de usuarios y gestion de contrasenas.
Codigo bajo prueba: app/routers/usuarios.py
"""
from conftest import auth_header


# --- Crear usuario (usuarios.py:60-77) ---

def test_crear_usuario_ok(client, admin_token):
    r = client.post("/usuarios/", headers=auth_header(admin_token), json={
        "nombreUsuario": "Nuevo",
        "apellidosUsuario": "Empleado",
        "emailUsuario": "nuevo@taskflow.com",
        "contraseñaUsuario": "secreta123",
        "rolUsuario": "usuario",
    })
    assert r.status_code == 200
    assert r.json()["emailUsuario"] == "nuevo@taskflow.com"


def test_crear_usuario_email_duplicado(client, admin_token, admin_user):
    r = client.post("/usuarios/", headers=auth_header(admin_token), json={
        "nombreUsuario": "Otro",
        "apellidosUsuario": "Admin",
        "emailUsuario": "admin@taskflow.com",
        "contraseñaUsuario": "secreta123",
        "rolUsuario": "usuario",
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "Ya existe un usuario con ese correo"


# --- Obtener usuario (usuarios.py:49-57) ---

def test_obtener_usuario_inexistente(client, admin_token):
    r = client.get("/usuarios/9999", headers=auth_header(admin_token))
    assert r.status_code == 404


def test_estandar_no_accede_a_otro_usuario(client, admin_user, standard_token):
    r = client.get(f"/usuarios/{admin_user.idUsuario}", headers=auth_header(standard_token))
    assert r.status_code == 403


def test_estandar_accede_a_su_propio_usuario(client, standard_user, standard_token):
    r = client.get(f"/usuarios/{standard_user.idUsuario}", headers=auth_header(standard_token))
    assert r.status_code == 200


# --- Actualizar usuario (usuarios.py:80-98) ---

def test_actualizar_usuario_ok(client, admin_token, standard_user):
    r = client.put(f"/usuarios/{standard_user.idUsuario}", headers=auth_header(admin_token),
                   json={"nombreUsuario": "Renombrado"})
    assert r.status_code == 200
    assert r.json()["nombreUsuario"] == "Renombrado"


def test_actualizar_usuario_inexistente(client, admin_token):
    r = client.put("/usuarios/9999", headers=auth_header(admin_token),
                   json={"nombreUsuario": "X"})
    assert r.status_code == 404


# --- Eliminar usuario (usuarios.py:135-156) ---

def test_eliminar_usuario_ok(client, admin_token, standard_user):
    r = client.delete(f"/usuarios/{standard_user.idUsuario}", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json()["mensaje"] == "Usuario eliminado correctamente"


def test_no_puede_eliminar_su_propio_usuario(client, admin_token, admin_user):
    r = client.delete(f"/usuarios/{admin_user.idUsuario}", headers=auth_header(admin_token))
    assert r.status_code == 400
    assert r.json()["detail"] == "No puedes eliminar tu propio usuario"


def test_eliminar_usuario_inexistente(client, admin_token):
    r = client.delete("/usuarios/9999", headers=auth_header(admin_token))
    assert r.status_code == 404


# --- Cambio de contrasena (usuarios.py:30-41) ---

def test_cambiar_contrasena_ok(client, standard_token):
    r = client.post("/usuarios/cambiar-contrasena", headers=auth_header(standard_token),
                    json={"contrasena_actual": "empleado123", "nueva_contrasena": "nueva123"})
    assert r.status_code == 200
    assert r.json()["mensaje"] == "Contraseña actualizada correctamente"


def test_cambiar_contrasena_actual_incorrecta(client, standard_token):
    r = client.post("/usuarios/cambiar-contrasena", headers=auth_header(standard_token),
                    json={"contrasena_actual": "equivocada123", "nueva_contrasena": "nueva123"})
    assert r.status_code == 400
    assert r.json()["detail"] == "La contraseña actual es incorrecta"
