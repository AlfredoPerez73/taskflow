from fastapi import APIRouter, Depends
from typing import List
from app.schemas.notificaciones import ActualizarPreferencias, RespuestaNotificacion, RespuestaPreferencias
from app.services import servicio_notificacion
from app.core.dependencias import obtener_usuario_actual

enrutador = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@enrutador.get("/", response_model=List[RespuestaNotificacion],
    summary="Listar mis notificaciones",
    description="Devuelve las últimas **50 notificaciones** del usuario autenticado, ordenadas por fecha descendente.")
async def listar(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.listar_notificaciones(usuario["_id"])


@enrutador.put("/leer-todas",
    summary="Marcar todas las notificaciones como leídas",
    description="Marca en masa todas las notificaciones no leídas del usuario. Devuelve el número de notificaciones afectadas.")
async def marcar_todas_leidas(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.marcar_todas_como_leidas(usuario["_id"])


@enrutador.put("/{notificacion_id}/leer", response_model=RespuestaNotificacion,
    summary="Marcar notificación individual como leída",
    description="Marca una notificación específica como leída. Solo el destinatario puede marcarla.")
async def marcar_leida(notificacion_id: str, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.marcar_como_leida(notificacion_id, usuario["_id"])


@enrutador.get("/preferencias", response_model=RespuestaPreferencias,
    summary="Obtener preferencias de notificación",
    description="Devuelve la configuración actual de qué eventos genera notificaciones y por qué canal (IN_APP, EMAIL, AMBOS).")
async def obtener_preferencias(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.obtener_preferencias(usuario["_id"])


@enrutador.put("/preferencias", response_model=RespuestaPreferencias,
    summary="Actualizar preferencias de notificación",
    description="Configura qué tipos de notificaciones recibe el usuario y por qué canal.")
async def actualizar_preferencias(datos: ActualizarPreferencias, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.actualizar_preferencias(usuario["_id"], datos)