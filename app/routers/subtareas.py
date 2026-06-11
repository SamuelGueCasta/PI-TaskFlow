from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Subtarea, UsuarioTarea, Usuario, Tarea
from app.schemas.schemas import SubtareaCreate, SubtareaUpdate, SubtareaOut
from app.routers.usuarios import get_current_user
from typing import List

router = APIRouter(prefix="/subtareas", tags=["Subtareas"])


@router.get("/tarea/{idTarea}", response_model=List[SubtareaOut])
def listar_subtareas(idTarea: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
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
    
    return db.query(Subtarea).filter(Subtarea.idTareaFK == idTarea).all()


@router.post("/", response_model=SubtareaOut)
def crear_subtarea(subtarea_data: SubtareaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    tarea = db.query(Tarea).filter(Tarea.idTarea == subtarea_data.idTareaFK).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    if current_user.rolUsuario != "admin":
        asignacion = db.query(UsuarioTarea).filter(
            UsuarioTarea.idTareaFK == subtarea_data.idTareaFK,
            UsuarioTarea.idUsuarioFK == current_user.idUsuario
        ).first()
        if not asignacion:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea")
    
    nueva_subtarea = Subtarea(
        tituloSubtarea=subtarea_data.tituloSubtarea,
        completadoSubtarea=False,
        idTareaFK=subtarea_data.idTareaFK
    )
    db.add(nueva_subtarea)
    db.commit()
    db.refresh(nueva_subtarea)
    return nueva_subtarea


@router.put("/{idSubtarea}", response_model=SubtareaOut)
def actualizar_subtarea(idSubtarea: int, subtarea_data: SubtareaUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    subtarea = db.query(Subtarea).filter(Subtarea.idSubtarea == idSubtarea).first()
    if not subtarea:
        raise HTTPException(status_code=404, detail="Subtarea no encontrada")
    
    if current_user.rolUsuario != "admin":
        asignacion = db.query(UsuarioTarea).filter(
            UsuarioTarea.idTareaFK == subtarea.idTareaFK,
            UsuarioTarea.idUsuarioFK == current_user.idUsuario
        ).first()
        if not asignacion:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta subtarea")
    
    if subtarea_data.tituloSubtarea is not None:
        subtarea.tituloSubtarea = subtarea_data.tituloSubtarea
    if subtarea_data.completadoSubtarea is not None:
        subtarea.completadoSubtarea = subtarea_data.completadoSubtarea
    
    db.commit()
    db.refresh(subtarea)
    return subtarea


@router.delete("/{idSubtarea}")
def eliminar_subtarea(idSubtarea: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    subtarea = db.query(Subtarea).filter(Subtarea.idSubtarea == idSubtarea).first()
    if not subtarea:
        raise HTTPException(status_code=404, detail="Subtarea no encontrada")
    
    if current_user.rolUsuario != "admin":
        asignacion = db.query(UsuarioTarea).filter(
            UsuarioTarea.idTareaFK == subtarea.idTareaFK,
            UsuarioTarea.idUsuarioFK == current_user.idUsuario
        ).first()
        if not asignacion:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta subtarea")
    
    db.delete(subtarea)
    db.commit()
    return {"mensaje": "Subtarea eliminada correctamente"}