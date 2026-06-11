from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Proyecto, Tarea, Usuario
from app.schemas.schemas import ProyectoCreate, ProyectoUpdate, ProyectoOut
from app.routers.usuarios import get_current_user, solo_admin
from typing import List

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


def _serializar_proyecto(proyecto: Proyecto, db: Session) -> dict:
    num_tareas = db.query(Tarea).filter(Tarea.idProyectoFK == proyecto.idProyecto).count()
    return {
        "idProyecto": proyecto.idProyecto,
        "nombreProyecto": proyecto.nombreProyecto,
        "descripcionProyecto": proyecto.descripcionProyecto,
        "fecha_inicioProyecto": proyecto.fecha_inicioProyecto,
        "fecha_finProyecto": proyecto.fecha_finProyecto,
        "idUsuarioFK": proyecto.idUsuarioFK,
        "num_tareas": num_tareas,
    }


@router.get("/", response_model=List[ProyectoOut])
def listar_proyectos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    proyectos = db.query(Proyecto).all()
    return [_serializar_proyecto(p, db) for p in proyectos]


@router.get("/{idProyecto}", response_model=ProyectoOut)
def obtener_proyecto(idProyecto: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == idProyecto).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return _serializar_proyecto(proyecto, db)


@router.post("/", response_model=ProyectoOut)
def crear_proyecto(proyecto_data: ProyectoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    # Validar fechas
    if proyecto_data.fecha_inicioProyecto and proyecto_data.fecha_finProyecto:
        if proyecto_data.fecha_finProyecto < proyecto_data.fecha_inicioProyecto:
            raise HTTPException(status_code=400, detail="La fecha de fin no puede ser anterior a la fecha de inicio")
    
    nuevo_proyecto = Proyecto(
        nombreProyecto=proyecto_data.nombreProyecto,
        descripcionProyecto=proyecto_data.descripcionProyecto,
        fecha_inicioProyecto=proyecto_data.fecha_inicioProyecto,
        fecha_finProyecto=proyecto_data.fecha_finProyecto,
        idUsuarioFK=current_user.idUsuario
    )
    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)
    return nuevo_proyecto


@router.put("/{idProyecto}", response_model=ProyectoOut)
def actualizar_proyecto(idProyecto: int, proyecto_data: ProyectoUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == idProyecto).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if proyecto_data.nombreProyecto is not None:
        proyecto.nombreProyecto = proyecto_data.nombreProyecto
    if proyecto_data.descripcionProyecto is not None:
        proyecto.descripcionProyecto = proyecto_data.descripcionProyecto
    if proyecto_data.fecha_inicioProyecto is not None:
        proyecto.fecha_inicioProyecto = proyecto_data.fecha_inicioProyecto
    if proyecto_data.fecha_finProyecto is not None:
        proyecto.fecha_finProyecto = proyecto_data.fecha_finProyecto
    
    # Validar fechas
    if proyecto.fecha_inicioProyecto and proyecto.fecha_finProyecto:
        if proyecto.fecha_finProyecto < proyecto.fecha_inicioProyecto:
            raise HTTPException(status_code=400, detail="La fecha de fin no puede ser anterior a la fecha de inicio")
    
    db.commit()
    db.refresh(proyecto)
    return proyecto


@router.delete("/{idProyecto}")
def eliminar_proyecto(idProyecto: int, db: Session = Depends(get_db), current_user: Usuario = Depends(solo_admin)):
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == idProyecto).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Comprobar si tiene tareas activas
    tareas_activas = db.query(Tarea).filter(
        Tarea.idProyectoFK == idProyecto,
        Tarea.estadoTarea != "finalizada"
    ).count()
    
    if tareas_activas > 0:
        raise HTTPException(status_code=400, detail=f"El proyecto tiene {tareas_activas} tarea(s) activa(s). Finalízalas antes de eliminar el proyecto")
    
    db.delete(proyecto)
    db.commit()
    return {"mensaje": "Proyecto eliminado correctamente"}