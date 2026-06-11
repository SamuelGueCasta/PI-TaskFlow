"""
Pruebas de caja blanca: control de acceso por rol.
Codigo bajo prueba: app/routers/usuarios.py (solo_admin) y app/routers/tareas.py
"""
from datetime import date, timedelta
from conftest import auth_header
from app.models.models import Proyecto, Tarea, UsuarioTarea


# --- Rutas exclusivas de administrador (usuarios.py:24-27) ---

def test_usuario_estandar_no_lista_usuarios(client, standard_token):
    r = client.get("/usuarios/", headers=auth_header(standard_token))
    assert r.status_code == 403
    assert r.json()["detail"] == "No tienes permisos para realizar esta acción"


def test_admin_si_lista_usuarios(client, admin_token):
    r = client.get("/usuarios/", headers=auth_header(admin_token))
    assert r.status_code == 200


def test_usuario_estandar_no_crea_proyecto(client, standard_token):
    r = client.post("/proyectos/", headers=auth_header(standard_token), json={
        "nombreProyecto": "Proyecto X",
    })
    assert r.status_code == 403


# --- Usuario estandar solo ve sus tareas asignadas (tareas.py:33-60) ---

def test_usuario_estandar_solo_ve_sus_tareas(client, db_session, admin_user, standard_user, standard_token):
    proyecto = Proyecto(nombreProyecto="P1", idUsuarioFK=admin_user.idUsuario)
    db_session.add(proyecto)
    db_session.commit()

    t_asignada = Tarea(tituloTarea="Mia", fecha_creacionTarea=date.today(),
                       estadoTarea="pendiente", prioridadTarea="media",
                       idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    t_ajena = Tarea(tituloTarea="Ajena", fecha_creacionTarea=date.today(),
                    estadoTarea="pendiente", prioridadTarea="media",
                    idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add_all([t_asignada, t_ajena])
    db_session.commit()
    db_session.add(UsuarioTarea(idTareaFK=t_asignada.idTarea, idUsuarioFK=standard_user.idUsuario))
    db_session.commit()

    r = client.get("/tareas/", headers=auth_header(standard_token))
    assert r.status_code == 200
    titulos = [t["tituloTarea"] for t in r.json()]
    assert "Mia" in titulos
    assert "Ajena" not in titulos


def test_usuario_estandar_no_accede_a_tarea_no_asignada(client, db_session, admin_user, standard_token):
    proyecto = Proyecto(nombreProyecto="P1", idUsuarioFK=admin_user.idUsuario)
    db_session.add(proyecto)
    db_session.commit()
    tarea = Tarea(tituloTarea="Ajena", fecha_creacionTarea=date.today(),
                  estadoTarea="pendiente", prioridadTarea="media",
                  idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()

    r = client.get(f"/tareas/{tarea.idTarea}", headers=auth_header(standard_token))
    assert r.status_code == 403
    assert r.json()["detail"] == "No tienes acceso a esta tarea"


# --- Usuario estandar no puede modificar campos restringidos (tareas.py:113-124) ---

def test_usuario_estandar_no_modifica_campos_restringidos(client, db_session, admin_user, standard_user, standard_token):
    proyecto = Proyecto(nombreProyecto="P1", idUsuarioFK=admin_user.idUsuario)
    db_session.add(proyecto)
    db_session.commit()
    tarea = Tarea(tituloTarea="T", fecha_creacionTarea=date.today(),
                  estadoTarea="pendiente", prioridadTarea="media",
                  idProyectoFK=proyecto.idProyecto, idUsuarioFK=admin_user.idUsuario)
    db_session.add(tarea)
    db_session.commit()
    db_session.add(UsuarioTarea(idTareaFK=tarea.idTarea, idUsuarioFK=standard_user.idUsuario))
    db_session.commit()

    r = client.put(f"/tareas/{tarea.idTarea}", headers=auth_header(standard_token),
                   json={"tituloTarea": "Nuevo titulo"})
    assert r.status_code == 403
