from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CrearTablero(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    proyectoId: str


class RenombrarTablero(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)


class CrearColumna(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    limiteWip: Optional[int] = Field(None, ge=1)


class ActualizarColumna(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=80)
    limiteWip: Optional[int] = Field(None, ge=1)
    posicion: Optional[int] = None


class RespuestaColumna(BaseModel):
    id: str
    nombre: str
    tableroId: str
    posicion: int
    limiteWip: Optional[int]


class RespuestaTablero(BaseModel):
    id: str
    nombre: str
    proyectoId: str
    esPorDefecto: bool
    columnas: List[RespuestaColumna] = []
    creadoEn: datetime