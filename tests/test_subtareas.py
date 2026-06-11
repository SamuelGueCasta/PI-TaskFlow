"""
Pruebas de caja blanca: CRUD de subtareas y control de acceso.
Codigo bajo prueba: app/routers/subtareas.py
"""
from datetime import date
from conftest import auth_header
from app.models.models import Proyecto, Tarea, Subtarea, UsuarioTarea


def _tarea(db_session, admin_user):
    proyecto = Proyecto(nombreProyecto="P", idUsuarioFK=admin_user.idUsuario)
    db_session.add(proyecto)
    db_session.commit()
    tarea = Tarea(tituloTarea="T", fecha_creacionTarea=date.today(), estadoTarea="pendiente",
                  prioridadTarea="media", idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()
    db_session.refresh(tarea)
    return tarea


# --- Crear subtarea (subtareas.py:29-51) ---

def test_crear_subtarea_ok(client, db_session, admin_user, admin_token):
    tarea = _tarea(db_session, admin_user)
    r = client.post("/subtareas/", headers=auth_header(admin_token), json={
        "tituloSubtarea": "Subtarea 1",
        "idTareaFK": tarea.idTarea,
    })
    assert r.status_code == 200
    assert r.json()["tituloSubtarea"] == "Subtarea 1"
    assert r.json()["completadoSubtarea"] is False


def test_crear_subtarea_tarea_inexistente(client, admin_token):
    r = client.post("/subtareas/", headers=auth_header(admin_token), json={
        "tituloSubtarea": "X",
        "idTareaFK": 9999,
    })
    assert r.status_code == 404
    assert r.json()["detail"] == "Tarea no encontrada"


def test_crear_subtarea_estandar_no_asignado(client, db_session, admin_user, standard_token):
    tarea = _tarea(db_session, admin_user)
    r = client.post("/subtareas/", headers=auth_header(standard_token), json={
        "tituloSubtarea": "X",
        "idTareaFK": tarea.idTarea,
    })
    assert r.status_code == 403


# --- Actualizar subtarea (subtareas.py:54-75) ---

def test_actualizar_subtarea_ok(client, db_session, admin_user, admin_token):
    tarea = _tarea(db_session, admin_user)
    sub = Subtarea(tituloSubtarea="Sub", completadoSubtarea=False, idTareaFK=tarea.idTarea)
    db_session.add(sub)
    db_session.commit()

    r = client.put(f"/subtareas/{sub.idSubtarea}", headers=auth_header(admin_token),
                   json={"completadoSubtarea": True, "tituloSubtarea": "Sub editada"})
    assert r.status_code == 200
    assert r.json()["completadoSubtarea"] is True
    assert r.json()["tituloSubtarea"] == "Sub editada"


def test_actualizar_subtarea_inexistente(client, admin_token):
    r = client.put("/subtareas/9999", headers=auth_header(admin_token),
                   json={"completadoSubtarea": True})
    assert r.status_code == 404


# --- Eliminar subtarea (subtareas.py:78-94) ---

def test_eliminar_subtarea_ok(client, db_session, admin_user, admin_token):
    tarea = _tarea(db_session, admin_user)
    sub = Subtarea(tituloSubtarea="Sub", completadoSubtarea=False, idTareaFK=tarea.idTarea)
    db_session.add(sub)
    db_session.commit()
    id_sub = sub.idSubtarea

    r = client.delete(f"/subtareas/{id_sub}", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert db_session.query(Subtarea).filter(Subtarea.idSubtarea == id_sub).first() is None


def test_eliminar_subtarea_inexistente(client, admin_token):
    r = client.delete("/subtareas/9999", headers=auth_header(admin_token))
    assert r.status_code == 404


# --- Listar subtareas (subtareas.py:12-26) ---

def test_listar_subtareas_estandar_no_asignado(client, db_session, admin_user, standard_token):
    tarea = _tarea(db_session, admin_user)
    r = client.get(f"/subtareas/tarea/{tarea.idTarea}", headers=auth_header(standard_token))
    assert r.status_code == 403


def test_listar_subtareas_estandar_asignado(client, db_session, admin_user, standard_user, standard_token):
    tarea = _tarea(db_session, admin_user)
    db_session.add(UsuarioTarea(idTareaFK=tarea.idTarea, idUsuarioFK=standard_user.idUsuario))
    db_session.add(Subtarea(tituloSubtarea="Sub", completadoSubtarea=False, idTareaFK=tarea.idTarea))
    db_session.commit()

    r = client.get(f"/subtareas/tarea/{tarea.idTarea}", headers=auth_header(standard_token))
    assert r.status_code == 200
    assert len(r.json()) == 1
