"""
Pruebas de caja blanca: CRUD de proyectos y validacion de fechas.
Codigo bajo prueba: app/routers/proyectos.py
"""
from datetime import date, timedelta
from conftest import auth_header


def _crear_proyecto(client, token, **kwargs):
    datos = {"nombreProyecto": "Proyecto Base"}
    datos.update(kwargs)
    return client.post("/proyectos/", headers=auth_header(token), json=datos)


# --- Crear proyecto (proyectos.py:39-56) ---

def test_crear_proyecto_admin_ok(client, admin_token):
    r = _crear_proyecto(client, admin_token, nombreProyecto="Proyecto A")
    assert r.status_code == 200
    assert r.json()["nombreProyecto"] == "Proyecto A"


def test_crear_proyecto_usuario_estandar_prohibido(client, standard_token):
    r = _crear_proyecto(client, standard_token)
    assert r.status_code == 403


# --- Validacion de fechas (proyectos.py:42-44, 75-77) ---

def test_crear_proyecto_fecha_fin_anterior_inicio(client, admin_token):
    hoy = date.today()
    r = _crear_proyecto(client, admin_token,
                        fecha_inicioProyecto=str(hoy),
                        fecha_finProyecto=str(hoy - timedelta(days=5)))
    assert r.status_code == 400
    assert "fecha de fin" in r.json()["detail"]


def test_actualizar_proyecto_fecha_fin_anterior_inicio(client, admin_token):
    hoy = date.today()
    creado = _crear_proyecto(client, admin_token,
                             fecha_inicioProyecto=str(hoy),
                             fecha_finProyecto=str(hoy + timedelta(days=5)))
    id_proyecto = creado.json()["idProyecto"]
    r = client.put(f"/proyectos/{id_proyecto}", headers=auth_header(admin_token),
                   json={"fecha_finProyecto": str(hoy - timedelta(days=1))})
    assert r.status_code == 400


# --- Actualizar / eliminar (proyectos.py:59-101) ---

def test_actualizar_proyecto_inexistente(client, admin_token):
    r = client.put("/proyectos/9999", headers=auth_header(admin_token),
                   json={"nombreProyecto": "X"})
    assert r.status_code == 404


def test_eliminar_proyecto_sin_tareas_ok(client, admin_token):
    creado = _crear_proyecto(client, admin_token, nombreProyecto="Para borrar")
    id_proyecto = creado.json()["idProyecto"]
    r = client.delete(f"/proyectos/{id_proyecto}", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json()["mensaje"] == "Proyecto eliminado correctamente"


def test_eliminar_proyecto_inexistente(client, admin_token):
    r = client.delete("/proyectos/9999", headers=auth_header(admin_token))
    assert r.status_code == 404
