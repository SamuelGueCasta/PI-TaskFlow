from sqlalchemy import Column, Integer, String, Enum, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuario"

    idUsuario = Column(Integer, primary_key=True, index=True)
    nombreUsuario = Column(String(255), nullable=False)
    apellidosUsuario = Column(String(255), nullable=False)
    emailUsuario = Column(String(255), unique=True, nullable=False)
    contraseñaUsuario = Column(String(255), nullable=False)
    rolUsuario = Column(Enum("admin", "usuario"), nullable=False)
    fotoUsuario = Column(String(255), nullable=True)

    proyectos = relationship("Proyecto", back_populates="creador")
    tareas_creadas = relationship("Tarea", back_populates="creador")
    recuperacion = relationship("RecuperacionContrasena", back_populates="usuario")
    tareas_asignadas = relationship("UsuarioTarea", back_populates="usuario")


class RecuperacionContrasena(Base):
    __tablename__ = "recuperacion_contraseña"

    idrecuperacion_contraseña = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False)
    expiracion = Column(DateTime, nullable=False)
    idUsuarioFK = Column(Integer, ForeignKey("usuario.idUsuario"), nullable=False)

    usuario = relationship("Usuario", back_populates="recuperacion")


class Proyecto(Base):
    __tablename__ = "proyecto"

    idProyecto = Column(Integer, primary_key=True, index=True)
    nombreProyecto = Column(String(255), nullable=False)
    descripcionProyecto = Column(String(255), nullable=True)
    fecha_inicioProyecto = Column(Date, nullable=True)
    fecha_finProyecto = Column(Date, nullable=True)
    idUsuarioFK = Column(Integer, ForeignKey("usuario.idUsuario"), nullable=False)

    creador = relationship("Usuario", back_populates="proyectos")
    tareas = relationship("Tarea", back_populates="proyecto")


class Tarea(Base):
    __tablename__ = "tarea"

    idTarea = Column(Integer, primary_key=True, index=True)
    tituloTarea = Column(String(245), nullable=False)
    descripcionTarea = Column(String(245), nullable=True)
    fecha_creacionTarea = Column(Date, nullable=False)
    estadoTarea = Column(Enum("pendiente", "en_proceso", "finalizada"), nullable=False, default="pendiente")
    prioridadTarea = Column(Enum("baja", "media", "alta"), nullable=False)
    fecha_limiteTarea = Column(Date, nullable=True)
    idProyectoFK = Column(Integer, ForeignKey("proyecto.idProyecto"), nullable=False)
    idUsuarioFK = Column(Integer, ForeignKey("usuario.idUsuario"), nullable=False)

    proyecto = relationship("Proyecto", back_populates="tareas")
    creador = relationship("Usuario", back_populates="tareas_creadas")
    subtareas = relationship("Subtarea", back_populates="tarea")
    usuarios_asignados = relationship("UsuarioTarea", back_populates="tarea")


class UsuarioTarea(Base):
    __tablename__ = "usuarios_tarea"

    idTareaFK = Column(Integer, ForeignKey("tarea.idTarea"), primary_key=True)
    idUsuarioFK = Column(Integer, ForeignKey("usuario.idUsuario"), primary_key=True)

    tarea = relationship("Tarea", back_populates="usuarios_asignados")
    usuario = relationship("Usuario", back_populates="tareas_asignadas")


class Subtarea(Base):
    __tablename__ = "subtarea"

    idSubtarea = Column(Integer, primary_key=True, index=True)
    tituloSubtarea = Column(String(245), nullable=False)
    completadoSubtarea = Column(Boolean, default=False)
    idTareaFK = Column(Integer, ForeignKey("tarea.idTarea"), nullable=False)

    tarea = relationship("Tarea", back_populates="subtareas")