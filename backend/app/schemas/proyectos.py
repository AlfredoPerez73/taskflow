from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from app.models.enums import EstadoProyecto


class CrearProyecto(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    descripcion: Optional[str] = None
    fechaInicio: date
    fechaFinEstimada: date


class ActualizarProyecto(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=120)
    descripcion: Optional[str] = None
    fechaFinEstimada: Optional[date] = None
    estado: Optional[EstadoProyecto] = None


class InvitarMiembro(BaseModel):
    email: str
    rolEnProyecto: str = "DEVELOPER"


class RespuestaProyecto(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str]
    fechaInicio: date
    fechaFinEstimada: date
    estado: str
    propietarioId: str
    estaArchivado: bool
    progreso: float = 0.0
    miembros: List[str] = []
    creadoEn: datetime


class RespuestaListaProyectos(BaseModel):
    proyectos: List[RespuestaProyecto]
    total: int