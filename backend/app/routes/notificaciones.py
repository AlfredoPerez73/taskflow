from fastapi import APIRouter, Depends
from app.schemas.notificaciones import ActualizarPreferencias
from app.services import servicio_notificacion
from app.core.dependencias import obtener_usuario_actual

enrutador = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@enrutador.get("/")
async def listar(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.listar_notificaciones(usuario["_id"])


@enrutador.put("/{notificacion_id}/leer")
async def marcar_leida(notificacion_id: str, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.marcar_como_leida(notificacion_id, usuario["_id"])


@enrutador.put("/leer-todas")
async def marcar_todas_leidas(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.marcar_todas_como_leidas(usuario["_id"])


@enrutador.get("/preferencias")
async def obtener_preferencias(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.obtener_preferencias(usuario["_id"])


@enrutador.put("/preferencias")
async def actualizar_preferencias(
    datos: ActualizarPreferencias,
    usuario: dict = Depends(obtener_usuario_actual),
):
    return await servicio_notificacion.actualizar_preferencias(usuario["_id"], datos)