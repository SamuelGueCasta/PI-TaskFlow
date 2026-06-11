from pydantic import BaseModel, EmailStr, StringConstraints
from typing import Optional, Annotated, List
from datetime import date, datetime
from enum import Enum

# ─── TIPOS REUTILIZABLES ─────────────────────────────────────────────────────
# TextoNoVacio: recorta espacios y exige al menos 1 carácter -> rechaza "" y "   "
# ContrasenaStr: exige al menos 6 caracteres (coherente con la validación del frontend);
# no recorta espacios para no alterar la contraseña que el usuario introduce.
TextoNoVacio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ContrasenaStr = Annotated[str, StringConstraints(min_length=6)]

# ─── ENUMS ───────────────────────────────────────────────────────────────────

class RolUsuario(str, Enum):
    admin = "admin"
    usuario = "usuario"

class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_proceso = "en_proceso"
    finalizada = "finalizada"

class PrioridadTarea(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

# ─── USUARIO ─────────────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombreUsuario: TextoNoVacio
    apellidosUsuario: TextoNoVacio
    emailUsuario: EmailStr
    contraseñaUsuario: ContrasenaStr
    rolUsuario: RolUsuario
    fotoUsuario: Optional[TextoNoVacio] = None

class UsuarioUpdate(BaseModel):
    nombreUsuario: Optional[TextoNoVacio] = None
    apellidosUsuario: Optional[TextoNoVacio] = None
    fotoUsuario: Optional[TextoNoVacio] = None

class UsuarioOut(BaseModel):
    idUsuario: int
    nombreUsuario: str
    apellidosUsuario: str
    emailUsuario: EmailStr
    rolUsuario: RolUsuario
    fotoUsuario: Optional[str] = None

    class Config:
        from_attributes = True

# ─── AUTH ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    emailUsuario: EmailStr
    contraseñaUsuario: ContrasenaStr

class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str
    idUsuario: int

class RecuperacionRequest(BaseModel):
    emailUsuario: EmailStr

class NuevaContrasenaRequest(BaseModel):
    token: TextoNoVacio
    nueva_contrasena: ContrasenaStr

class CambiarContrasenaRequest(BaseModel):
    contrasena_actual: ContrasenaStr
    nueva_contrasena: ContrasenaStr

# ─── PROYECTO ────────────────────────────────────────────────────────────────

class ProyectoCreate(BaseModel):
    nombreProyecto: TextoNoVacio
    descripcionProyecto: Optional[TextoNoVacio] = None
    fecha_inicioProyecto: Optional[date] = None
    fecha_finProyecto: Optional[date] = None

class ProyectoUpdate(BaseModel):
    nombreProyecto: Optional[TextoNoVacio] = None
    descripcionProyecto: Optional[TextoNoVacio] = None
    fecha_inicioProyecto: Optional[date] = None
    fecha_finProyecto: Optional[date] = None

class ProyectoOut(BaseModel):
    idProyecto: int
    nombreProyecto: str
    descripcionProyecto: Optional[str] = None
    fecha_inicioProyecto: Optional[date] = None
    fecha_finProyecto: Optional[date] = None
    idUsuarioFK: int
    num_tareas: int = 0

    class Config:
        from_attributes = True

# ─── TAREA ───────────────────────────────────────────────────────────────────

class TareaCreate(BaseModel):
    tituloTarea: TextoNoVacio
    descripcionTarea: Optional[TextoNoVacio] = None
    prioridadTarea: PrioridadTarea
    fecha_limiteTarea: Optional[date] = None
    idProyectoFK: int
    usuarios_asignados: Optional[list[int]] = []

class TareaUpdate(BaseModel):
    tituloTarea: Optional[TextoNoVacio] = None
    descripcionTarea: Optional[TextoNoVacio] = None
    estadoTarea: Optional[EstadoTarea] = None
    prioridadTarea: Optional[PrioridadTarea] = None
    fecha_limiteTarea: Optional[date] = None

class TareaOut(BaseModel):
    idTarea: int
    tituloTarea: str
    descripcionTarea: Optional[str] = None
    fecha_creacionTarea: date
    estadoTarea: EstadoTarea
    prioridadTarea: PrioridadTarea
    fecha_limiteTarea: Optional[date] = None
    idProyectoFK: int
    idUsuarioFK: int
    nombreProyecto: str
    usuarios_asignados: List[int]

    class Config:
        from_attributes = True

# ─── SUBTAREA ────────────────────────────────────────────────────────────────

class SubtareaCreate(BaseModel):
    tituloSubtarea: TextoNoVacio
    idTareaFK: int

class SubtareaUpdate(BaseModel):
    tituloSubtarea: Optional[TextoNoVacio] = None
    completadoSubtarea: Optional[bool] = None

class SubtareaOut(BaseModel):
    idSubtarea: int
    tituloSubtarea: str
    completadoSubtarea: bool
    idTareaFK: int

    class Config:
        from_attributes = True
