from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.enums import TipoNotificacion, CanalNotificacion


class RespuestaNotificacion(BaseModel):
    id: str
    usuarioId: str
    mensaje: str
    tipo: str
    leida: bool
    creadoEn: datetime
    tareaId: Optional[str] = None
    proyectoId: Optional[str] = None
    tituloTarea: Optional[str] = None


class ActualizarPreferencias(BaseModel):
    notificacionAsignacion: Optional[bool] = None
    notificacionVencimiento: Optional[bool] = None
    notificacionComentario: Optional[bool] = None
    notificacionCambioEstado: Optional[bool] = None
    canal: Optional[CanalNotificacion] = None


class RespuestaPreferencias(BaseModel):
    usuarioId: str
    notificacionAsignacion: bool
    notificacionVencimiento: bool
    notificacionComentario: bool
    notificacionCambioEstado: bool
    canal: str