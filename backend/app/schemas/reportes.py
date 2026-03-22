from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class RespuestaMetricasProyecto(BaseModel):
    proyectoId: str
    totalTareas: int
    tareasPorEstado: Dict[str, int]
    tareasPorUsuario: Dict[str, int]
    tareasVencidas: int
    tareasCompletadas: int = 0
    progreso: float
    velocidadPorSemana: List[Dict[str, Any]]
    # Campos nuevos — opcionales para compatibilidad con datos viejos
    tareasPorPrioridad: Dict[str, int] = {}
    tareasPorTipo: Dict[str, int] = {}


class FiltroTareas(BaseModel):
    texto: Optional[str] = None
    responsableId: Optional[str] = None
    etiqueta: Optional[str] = None
    prioridad: Optional[str] = None
    tipo: Optional[str] = None
    fechaDesde: Optional[datetime] = None
    fechaHasta: Optional[datetime] = None


class GuardarFiltro(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    proyectoId: str
    criterios: FiltroTareas


class RespuestaFiltroGuardado(BaseModel):
    id: str
    nombre: str
    proyectoId: str
    usuarioId: str
    criterios: dict


class RespuestaEntradaAuditoria(BaseModel):
    id: str
    tipoEntidad: str
    entidadId: str
    accion: str
    usuarioId: str
    valorAnterior: Optional[dict] = None
    valorNuevo: Optional[dict] = None
    marca: datetime


class RespuestaConfiguracion(BaseModel):
    nombrePlataforma: str
    tamanoMaxArchivoMb: int
    politicaContrasena: dict
    zona_horaria: str


class ActualizarConfiguracion(BaseModel):
    nombrePlataforma: Optional[str] = None
    tamanoMaxArchivoMb: Optional[int] = Field(None, ge=1, le=100)
    zona_horaria: Optional[str] = None
    tema: Optional[str] = None
    politicaContrasena: Optional[dict] = None