"""
Pruebas de caja blanca: CRUD de tareas, asignaciones, fechas y subtareas pendientes.
Codigo bajo prueba: app/routers/tareas.py
"""
from datetime import date, timedelta
from conftest import auth_header
from app.models.models import Proyecto, Tarea, Subtarea


def _proyecto(db_session, admin_user, fecha_fin=None):
    proyecto = Proyecto(nombreProyecto="P", idUsuarioFK=admin_user.idUsuario,
                        fecha_finProyecto=fecha_fin)
    db_session.add(proyecto)
    db_session.commit()
    db_session.refresh(proyecto)
    return proyecto


# --- Crear tarea con validaciones de fecha (tareas.py:63-104) ---

def test_crear_tarea_ok(client, db_session, admin_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    r = client.post("/tareas/", headers=auth_header(admin_token), json={
        "tituloTarea": "Tarea 1",
        "prioridadTarea": "media",
        "idProyectoFK": proyecto.idProyecto,
        "usuarios_asignados": [admin_user.idUsuario],
    })
    assert r.status_code == 200
    assert r.json()["usuarios_asignados"] == [admin_user.idUsuario]
    assert r.json()["estadoTarea"] == "pendiente"


def test_crear_tarea_fecha_limite_pasada(client, db_session, admin_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    r = client.post("/tareas/", headers=auth_header(admin_token), json={
        "tituloTarea": "Tarea",
        "prioridadTarea": "media",
        "fecha_limiteTarea": str(date.today() - timedelta(days=1)),
        "idProyectoFK": proyecto.idProyecto,
    })
    assert r.status_code == 400
    assert "fecha límite no puede ser anterior a hoy" in r.json()["detail"]


def test_crear_tarea_proyecto_inexistente(client, admin_token):
    r = client.post("/tareas/", headers=auth_header(admin_token), json={
        "tituloTarea": "Tarea",
        "prioridadTarea": "media",
        "idProyectoFK": 9999,
    })
    assert r.status_code == 404
    assert r.json()["detail"] == "Proyecto no encontrado"


def test_crear_tarea_fecha_limite_posterior_fin_proyecto(client, db_session, admin_user, admin_token):
    proyecto = _proyecto(db_session, admin_user, fecha_fin=date.today() + timedelta(days=5))
    r = client.post("/tareas/", headers=auth_header(admin_token), json={
        "tituloTarea": "Tarea",
        "prioridadTarea": "media",
        "fecha_limiteTarea": str(date.today() + timedelta(days=10)),
        "idProyectoFK": proyecto.idProyecto,
    })
    assert r.status_code == 400
    assert "fecha de fin del proyecto" in r.json()["detail"]


def test_crear_tarea_usuario_asignado_inexistente_no_persiste(client, db_session, admin_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    r = client.post("/tareas/", headers=auth_header(admin_token), json={
        "tituloTarea": "Tarea fantasma",
        "prioridadTarea": "media",
        "idProyectoFK": proyecto.idProyecto,
        "usuarios_asignados": [9999],
    })
    assert r.status_code == 404
    # La tarea no debe haberse guardado
    assert db_session.query(Tarea).filter(Tarea.tituloTarea == "Tarea fantasma").first() is None


# --- Finalizar tarea con subtareas pendientes (tareas.py:149-155) ---

def test_no_finaliza_tarea_con_subtareas_pendientes(client, db_session, admin_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    tarea = Tarea(tituloTarea="T", fecha_creacionTarea=date.today(), estadoTarea="pendiente",
                  prioridadTarea="media", idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()
    db_session.add(Subtarea(tituloSubtarea="Sub", completadoSubtarea=False, idTareaFK=tarea.idTarea))
    db_session.commit()

    r = client.put(f"/tareas/{tarea.idTarea}", headers=auth_header(admin_token),
                   json={"estadoTarea": "finalizada"})
    assert r.status_code == 400
    assert "subtarea" in r.json()["detail"]


def test_finaliza_tarea_sin_subtareas_pendientes(client, db_session, admin_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    tarea = Tarea(tituloTarea="T", fecha_creacionTarea=date.today(), estadoTarea="pendiente",
                  prioridadTarea="media", idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()
    db_session.add(Subtarea(tituloSubtarea="Sub", completadoSubtarea=True, idTareaFK=tarea.idTarea))
    db_session.commit()

    r = client.put(f"/tareas/{tarea.idTarea}", headers=auth_header(admin_token),
                   json={"estadoTarea": "finalizada"})
    assert r.status_code == 200
    assert r.json()["estadoTarea"] == "finalizada"


# --- Asignar / desasignar (tareas.py:182-216) ---

def test_asignar_usuario_ok(client, db_session, admin_user, standard_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    tarea = Tarea(tituloTarea="T", fecha_creacionTarea=date.today(), estadoTarea="pendiente",
                  prioridadTarea="media", idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()

    r = client.post(f"/tareas/{tarea.idTarea}/asignar/{standard_user.idUsuario}",
                    headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json()["mensaje"] == "Usuario asignado correctamente"


def test_asignar_usuario_ya_asignado(client, db_session, admin_user, standard_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    tarea = Tarea(tituloTarea="T", fecha_creacionTarea=date.today(), estadoTarea="pendiente",
                  prioridadTarea="media", idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()
    client.post(f"/tareas/{tarea.idTarea}/asignar/{standard_user.idUsuario}", headers=auth_header(admin_token))

    r = client.post(f"/tareas/{tarea.idTarea}/asignar/{standard_user.idUsuario}", headers=auth_header(admin_token))
    assert r.status_code == 400
    assert r.json()["detail"] == "El usuario ya está asignado a esta tarea"


def test_desasignar_usuario_no_asignado(client, db_session, admin_user, standard_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    tarea = Tarea(tituloTarea="T", fecha_creacionTarea=date.today(), estadoTarea="pendiente",
                  prioridadTarea="media", idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()

    r = client.delete(f"/tareas/{tarea.idTarea}/desasignar/{standard_user.idUsuario}",
                      headers=auth_header(admin_token))
    assert r.status_code == 404


# --- Eliminar tarea (tareas.py:169-179) ---

def test_eliminar_tarea_ok(client, db_session, admin_user, admin_token):
    proyecto = _proyecto(db_session, admin_user)
    tarea = Tarea(tituloTarea="T", fecha_creacionTarea=date.today(), estadoTarea="pendiente",
                  prioridadTarea="media", idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()
    id_tarea = tarea.idTarea

    r = client.delete(f"/tareas/{id_tarea}", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert db_session.query(Tarea).filter(Tarea.idTarea == id_tarea).first() is None


def test_eliminar_tarea_inexistente(client, admin_token):
    r = client.delete("/tareas/9999", headers=auth_header(admin_token))
    assert r.status_code == 404
