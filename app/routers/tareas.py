from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Tarea, UsuarioTarea, Usuario, Subtarea, Proyecto
from app.schemas.schemas import TareaCreate, TareaUpdate, TareaOut
from app.routers.usuarios import get_current_user, solo_admin
from typing import List
from datetime import date

router = APIRouter(prefix="/tareas", tags=["Tareas"])


def _serializar_tarea(tarea: Tarea, db: Session) -> dict:
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == tarea.idProyectoFK).first()
    asignaciones = db.query(UsuarioTarea.idUsuarioFK).filter(
        UsuarioTarea.idTareaFK == tarea.idTarea
    ).all()
    return {
        "idTarea": tarea.idTarea,
        "tituloTarea": tarea.tituloTarea,
        "descripcionTarea": tarea.descripcionTarea,
        "fecha_creacionTarea": tarea.fecha_creacionTarea,
        "estadoTarea": tarea.estadoTarea,
        "prioridadTarea": tarea.prioridadTarea,
        "fecha_limiteTarea": tarea.fecha_limiteTarea,
        "idProyectoFK": tarea.idProyectoFK,
        "idUsuarioFK": tarea.idUsuarioFK,
        "nombreProyecto": proyecto.nombreProyecto if proyecto else "",
        "usuarios_asignados": [a[0] for a in asignaciones],
    }


@router.get("/", response_model=List[TareaOut])
def listar_tareas(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rolUsuario == "admin":
        tareas = db.query(Tarea).all()
    else:
        tareas_ids = db.query(UsuarioTarea.idTareaFK).filter(
            UsuarioTarea.idUsuarioFK == current_user.idUsuario
        ).all()
        ids = [t[0] for t in tareas_ids]
        tareas = db.query(Tarea).filter(Tarea.idTarea.in_(ids)).all()
    return [_serializar_tarea(t, db) for t in tareas]


@router.get("/{idTarea}", response_model=TareaOut)
def obtener_tarea(idTarea: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    tarea = db.query(Tarea).filter(Tarea.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    if current_user.rolUsuario != "admin":
        asignacion = db.query(UsuarioTarea).filter(
            UsuarioTarea.idTareaFK == idTarea,
            UsuarioTarea.idUsuarioFK == current_user.idUsuario
        ).first()
        if not asignacion:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea")

    return _serializar_tarea(tarea, db)


@router.post("/", response_model=TareaOut)
def crear_tarea(tarea_data: TareaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    # Validar fecha límite
    if tarea_data.fecha_limiteTarea:
        if tarea_data.fecha_limiteTarea < date.today():
            raise HTTPException(status_code=400, detail="La fecha límite no puede ser anterior a hoy")

    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == tarea_data.idProyectoFK).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Validar que la fecha límite no sea posterior a la fecha de fin del proyecto
    if tarea_data.fecha_limiteTarea and proyecto.fecha_finProyecto and tarea_data.fecha_limiteTarea > proyecto.fecha_finProyecto:
        raise HTTPException(status_code=400, detail="La fecha límite de la tarea no puede ser posterior a la fecha de fin del proyecto")

    # Validar que todos los usuarios a asignar existen ANTES de crear la tarea
    # para evitar dejar una tarea persistida si alguno no existe.
    for idUsuario in tarea_data.usuarios_asignados:
        existe_usuario = db.query(Usuario).filter(Usuario.idUsuario == idUsuario).first()
        if not existe_usuario:
            raise HTTPException(status_code=404, detail=f"Usuario con id {idUsuario} no encontrado")

    nueva_tarea = Tarea(
        tituloTarea=tarea_data.tituloTarea,
        descripcionTarea=tarea_data.descripcionTarea,
        fecha_creacionTarea=date.today(),
        estadoTarea="pendiente",
        prioridadTarea=tarea_data.prioridadTarea,
        fecha_limiteTarea=tarea_data.fecha_limiteTarea,
        idProyectoFK=tarea_data.idProyectoFK,
        idUsuarioFK=current_user.idUsuario
    )
    db.add(nueva_tarea)
    db.flush()

    for idUsuario in tarea_data.usuarios_asignados:
        asignacion = UsuarioTarea(idTareaFK=nueva_tarea.idTarea, idUsuarioFK=idUsuario)
        db.add(asignacion)

    db.commit()
    db.refresh(nueva_tarea)
    return _serializar_tarea(nueva_tarea, db)


@router.put("/{idTarea}", response_model=TareaOut)
def actualizar_tarea(idTarea: int, tarea_data: TareaUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    tarea = db.query(Tarea).filter(Tarea.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    if current_user.rolUsuario != "admin":
        campos_restringidos = [
            tarea_data.tituloTarea,
            tarea_data.descripcionTarea,
            tarea_data.prioridadTarea,
            tarea_data.fecha_limiteTarea
        ]
        if any(campo is not None for campo in campos_restringidos):
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para modificar estos campos. Solo puedes cambiar el estado de la tarea"
            )

    if current_user.rolUsuario == "admin":
        if tarea_data.tituloTarea is not None:
            tarea.tituloTarea = tarea_data.tituloTarea
        if tarea_data.descripcionTarea is not None:
            tarea.descripcionTarea = tarea_data.descripcionTarea
        if tarea_data.prioridadTarea is not None:
            tarea.prioridadTarea = tarea_data.prioridadTarea
        if tarea_data.fecha_limiteTarea is not None:
            if tarea_data.fecha_limiteTarea < date.today():
                raise HTTPException(status_code=400, detail="La fecha límite no puede ser anterior a hoy")
            tarea.fecha_limiteTarea = tarea_data.fecha_limiteTarea
    
    # Tanto admin como usuario pueden actualizar el estado
    if tarea_data.estadoTarea is not None:
        if current_user.rolUsuario != "admin":
            asignacion = db.query(UsuarioTarea).filter(
                UsuarioTarea.idTareaFK == idTarea,
                UsuarioTarea.idUsuarioFK == current_user.idUsuario
            ).first()
            if not asignacion:
                raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea")
        
        # Comprobar subtareas si se quiere finalizar
        if tarea_data.estadoTarea == "finalizada":
            subtareas_pendientes = db.query(Subtarea).filter(
                Subtarea.idTareaFK == idTarea,
                Subtarea.completadoSubtarea == False
            ).count()
            if subtareas_pendientes > 0:
                raise HTTPException(status_code=400, detail=f"Hay {subtareas_pendientes} subtarea(s) pendiente(s). Complétalas antes de finalizar la tarea")
        
        tarea.estadoTarea = tarea_data.estadoTarea

    # Validar que la fecha límite no sea posterior a la fecha de fin del proyecto
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == tarea.idProyectoFK).first()
    if tarea.fecha_limiteTarea and proyecto and proyecto.fecha_finProyecto and tarea.fecha_limiteTarea > proyecto.fecha_finProyecto:
        raise HTTPException(status_code=400, detail="La fecha límite de la tarea no puede ser posterior a la fecha de fin del proyecto")

    db.commit()
    db.refresh(tarea)
    return _serializar_tarea(tarea, db)


@router.delete("/{idTarea}")
def eliminar_tarea(idTarea: int, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    tarea = db.query(Tarea).filter(Tarea.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    db.query(UsuarioTarea).filter(UsuarioTarea.idTareaFK == idTarea).delete()
    db.query(Subtarea).filter(Subtarea.idTareaFK == idTarea).delete()
    db.delete(tarea)
    db.commit()
    return {"mensaje": "Tarea eliminada correctamente"}


@router.post("/{idTarea}/asignar/{idUsuario}")
def asignar_usuario(idTarea: int, idUsuario: int, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    tarea = db.query(Tarea).filter(Tarea.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    usuario = db.query(Usuario).filter(Usuario.idUsuario == idUsuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    existe = db.query(UsuarioTarea).filter(
        UsuarioTarea.idTareaFK == idTarea,
        UsuarioTarea.idUsuarioFK == idUsuario
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="El usuario ya está asignado a esta tarea")
    
    asignacion = UsuarioTarea(idTareaFK=idTarea, idUsuarioFK=idUsuario)
    db.add(asignacion)
    db.commit()
    return {"mensaje": "Usuario asignado correctamente"}


@router.delete("/{idTarea}/desasignar/{idUsuario}")
def desasignar_usuario(idTarea: int, idUsuario: int, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    asignacion = db.query(UsuarioTarea).filter(
        UsuarioTarea.idTareaFK == idTarea,
        UsuarioTarea.idUsuarioFK == idUsuario
    ).first()
    if not asignacion:
        raise HTTPException(status_code=404, detail="El usuario no está asignado a esta tarea")
    
    db.delete(asignacion)
    db.commit()
    return {"mensaje": "Usuario desasignado correctamente"}