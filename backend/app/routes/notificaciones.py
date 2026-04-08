"""
Rutas de notificaciones.
Incluye:
  - CRUD estándar (listar, marcar leída, preferencias)
  - POST /enviar-externo: Factory Method + Adapter
  - PUT  /contacto:       guardar teléfonos para WhatsApp/SMS
  - POST /probar-canales: prueba todos los canales
  - GET  /stream:         SSE en tiempo real
"""
import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import List

from app.schemas.notificaciones import ActualizarPreferencias, RespuestaNotificacion, RespuestaPreferencias
from app.services import servicio_notificacion
from app.core.dependencias import obtener_usuario_actual, requerir_rol

enrutador = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


# ─── CRUD ────────────────────────────────────────────

@enrutador.get("/", response_model=List[RespuestaNotificacion],
    summary="Listar mis notificaciones")
async def listar(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.listar_notificaciones(usuario["_id"])


@enrutador.put("/leer-todas",
    summary="Marcar todas las notificaciones como leídas")
async def marcar_todas_leidas(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.marcar_todas_como_leidas(usuario["_id"])


@enrutador.put("/{notificacion_id}/leer", response_model=RespuestaNotificacion,
    summary="Marcar notificación individual como leída")
async def marcar_leida(notificacion_id: str, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.marcar_como_leida(notificacion_id, usuario["_id"])


# ─── PREFERENCIAS ────────────────────────────────────

@enrutador.get("/preferencias", response_model=RespuestaPreferencias,
    summary="Obtener preferencias de notificación")
async def obtener_preferencias(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.obtener_preferencias(usuario["_id"])


@enrutador.put("/preferencias", response_model=RespuestaPreferencias,
    summary="Actualizar preferencias de notificación",
    description="Configura canal (IN_APP | EMAIL | AMBOS) y qué tipos activan notificación.")
async def actualizar_preferencias(datos: ActualizarPreferencias, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.actualizar_preferencias(usuario["_id"], datos)


@enrutador.put("/contacto",
    summary="Actualizar datos de contacto para canales externos",
    description="Guarda el teléfono de WhatsApp y/o SMS para recibir notificaciones externas.")
async def actualizar_contacto(body: dict, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_notificacion.actualizar_contacto_externo(
        usuario["_id"],
        body.get("telefonoWhatsapp"),
        body.get("telefonoSms"),
    )


# ─── ENVÍO EXTERNO ───────────────────────────────────

@enrutador.post("/enviar-externo",
    summary="Enviar notificación por canal externo — Factory Method + Adapter",
    description="""
Envía una notificación usando el patrón **Factory Method** para seleccionar
la fábrica del canal y **Adapter** para traducir a la API externa.

**Canales:** `email`, `whatsapp`, `sms`

Cuerpo JSON:
```json
{
  "canal": "email",
  "mensaje": "Tu tarea fue actualizada",
  "usuarioId": "uuid-del-destinatario",
  "asunto": "Notificación TaskFlow"
}
```
""")
async def enviar_notificacion_externa(
    body: dict,
    usuario: dict = Depends(requerir_rol("ADMIN", "PROJECT_MANAGER")),
):
    canal   = body.get("canal", "email")
    mensaje = body.get("mensaje", "")
    user_id = body.get("usuarioId", usuario["_id"])
    asunto  = body.get("asunto", "Notificación TaskFlow")

    return await servicio_notificacion.enviar_notificacion_externa(
        usuario_id=user_id,
        mensaje=mensaje,
        canal=canal,
        asunto=asunto,
    )


@enrutador.post("/probar-canales",
    summary="Probar todos los canales de notificación",
    description="Envía un mensaje de prueba por email, whatsapp y sms para verificar la configuración.")
async def probar_canales(
    body: dict,
    usuario: dict = Depends(requerir_rol("ADMIN", "PROJECT_MANAGER")),
):
    user_id = body.get("usuarioId", usuario["_id"])
    mensaje = body.get("mensaje", "Prueba de canal TaskFlow 🔔")
    return await servicio_notificacion.probar_canales(user_id, mensaje)


# ─── SSE ─────────────────────────────────────────────

@enrutador.get("/stream",
    summary="Stream SSE de notificaciones en tiempo real",
    description="Abre una conexión Server-Sent Events. El cliente recibe eventos en tiempo real.")
async def stream_notificaciones(usuario: dict = Depends(obtener_usuario_actual)):
    try:
        from app.core.gestor_eventos import gestor_eventos, evento_ping
        _sse_disponible = True
    except ImportError:
        _sse_disponible = False

    async def generador():
        if not _sse_disponible:
            yield "data: {\"tipo\":\"ping\"}\n\n"
            return

        q = gestor_eventos.suscribir_usuario(usuario["_id"])
        try:
            yield f"data: {json.dumps({'tipo': 'conectado', 'usuarioId': usuario['_id']})}\n\n"
            while True:
                try:
                    evento = await asyncio.wait_for(q.get(), timeout=25)
                    yield f"data: {json.dumps(evento, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps(evento_ping())}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            gestor_eventos.desuscribir_usuario(usuario["_id"], q)

    return StreamingResponse(
        generador(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )