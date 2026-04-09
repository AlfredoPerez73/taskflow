from fastapi import APIRouter, Depends, Body
from typing import List
from app.schemas.notificaciones import ActualizarPreferencias, RespuestaNotificacion, RespuestaPreferencias
from app.services import servicio_notificacion
from app.core.dependencias import obtener_usuario_actual, requerir_rol

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


@enrutador.post(
    "/enviar-externo",
    summary="Enviar notificación por canal externo — Factory Method + Adapter",
    description="""
Envía una notificación usando **Factory Method** para seleccionar la fábrica
del canal y **Adapter** para traducir la solicitud a la API externa.

**Canales disponibles:** `email`, `whatsapp`, `sms`

**Flujo:**
1. `ProveedorNotificacion.get(canal)` → fábrica concreta (Factory Method)
2. `fabrica.get()` → adaptador concreto (Factory Method)
3. `adapter.enviar(solicitud)` → API externa (Adapter)
""",
)
async def enviar_notificacion_externa(
    body: dict = Body(..., example={"canal": "email", "mensaje": "Hola", "usuarioId": "uuid"}),
    usuario: dict = Depends(requerir_rol("ADMIN", "PROJECT_MANAGER")),
):
    canal    = body.get("canal", "email")
    mensaje  = body.get("mensaje", "")
    user_id  = body.get("usuarioId", usuario["_id"])
    asunto   = body.get("asunto", "Notificación TaskFlow")

    contacto = body.get("contacto", None)  # numero telefono para WhatsApp/SMS

    resultado = await servicio_notificacion.enviar_notificacion_externa(
        usuario_id=user_id,
        mensaje=mensaje,
        canal=canal,
        asunto=asunto,
        contacto_directo=contacto,
    )
    return resultado


@enrutador.post(
    "/probar-canales",
    summary="Probar todos los canales — Factory Method + Adapter",
    description="Envia un mensaje de prueba por email, whatsapp y sms para verificar configuracion.",
)
async def probar_todos_canales(
    body: dict = Body(default={}),
    usuario: dict = Depends(requerir_rol("ADMIN", "PROJECT_MANAGER")),
):
    user_id           = body.get("usuarioId", usuario["_id"])
    mensaje           = body.get("mensaje", "Prueba de canal TaskFlow")
    contacto_wa       = body.get("contactoWhatsapp")
    contacto_sms      = body.get("contactoSms")

    return await servicio_notificacion.probar_canales(
        usuario_id=user_id,
        mensaje=mensaje,
        contacto_whatsapp=contacto_wa,
        contacto_sms=contacto_sms,
    )