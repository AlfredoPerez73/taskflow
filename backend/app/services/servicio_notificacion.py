from datetime import datetime, timezone
from fastapi import HTTPException
import uuid

from app.db.conexion import ConexionMongoDB
from app.schemas.notificaciones import ActualizarPreferencias
from app.patterns.adapter.notificacion_adapter import SolicitudNotificacion
from app.patterns.adapter.proveedor_notificacion import ProveedorNotificacion

# Instancia única del proveedor (reutilizable)
_proveedor_notificacion = ProveedorNotificacion()
# gestor_eventos es opcional (SSE en tiempo real)
# Si no existe el archivo, las notificaciones funcionan igual (solo sin push)
try:
    from app.core.gestor_eventos import gestor_eventos, evento_notificacion
    _SSE_ACTIVO = True
except ImportError:
    gestor_eventos = None
    evento_notificacion = lambda n: {}
    _SSE_ACTIVO = False


def _db():
    return ConexionMongoDB.obtener_instancia().obtener_base_datos()


def _serializar(doc: dict) -> dict:
    return {
        "id":         doc["_id"],
        "usuarioId":  doc["usuarioId"],
        "mensaje":    doc["mensaje"],
        "tipo":       doc["tipo"],
        "leida":      doc.get("leida", False),
        "creadoEn":   doc["creadoEn"],
        # Metadatos de navegación — pueden ser None para notificaciones antiguas
        "tareaId":    doc.get("tareaId"),
        "proyectoId": doc.get("proyectoId"),
        "tituloTarea": doc.get("tituloTarea"),
    }


async def crear_notificacion_interna(
    db,
    usuario_id: str,
    mensaje: str,
    tipo: str,
    *,
    tarea_id: str | None = None,
    proyecto_id: str | None = None,
    titulo_tarea: str | None = None,
) -> None:
    """
    Crea una notificación interna con metadatos opcionales de navegación.
    Incluir tarea_id y proyecto_id permite al frontend navegar directo a la tarea.
    """
    notif = {
        "_id":         str(uuid.uuid4()),
        "usuarioId":   usuario_id,
        "mensaje":     mensaje,
        "tipo":        tipo,
        "leida":       False,
        "creadoEn":    datetime.now(timezone.utc),
        "tareaId":     tarea_id,
        "proyectoId":  proyecto_id,
        "tituloTarea": titulo_tarea,
    }
    await db["notificaciones"].insert_one(notif)
    if _SSE_ACTIVO and gestor_eventos:
        gestor_eventos.publicar_a_usuario(usuario_id, evento_notificacion(notif))


async def listar_notificaciones(usuario_id: str) -> list:
    db = _db()
    cursor = db["notificaciones"].find(
        {"usuarioId": usuario_id},
        sort=[("creadoEn", -1)],
        limit=50,
    )
    return [_serializar(n) async for n in cursor]


async def marcar_como_leida(notificacion_id: str, usuario_id: str) -> dict:
    db = _db()
    notif = await db["notificaciones"].find_one({"_id": notificacion_id})
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if notif["usuarioId"] != usuario_id:
        raise HTTPException(status_code=403, detail="Sin acceso a esta notificación")
    await db["notificaciones"].update_one(
        {"_id": notificacion_id}, {"$set": {"leida": True}}
    )
    notif["leida"] = True
    return _serializar(notif)


async def marcar_todas_como_leidas(usuario_id: str) -> dict:
    db = _db()
    resultado = await db["notificaciones"].update_many(
        {"usuarioId": usuario_id, "leida": False},
        {"$set": {"leida": True}},
    )
    return {"mensaje": f"{resultado.modified_count} notificaciones marcadas como leídas"}


async def obtener_preferencias(usuario_id: str) -> dict:
    db = _db()
    prefs = await db["preferencias_notificacion"].find_one({"usuarioId": usuario_id})
    if not prefs:
        return {
            "usuarioId": usuario_id,
            "notificacionAsignacion":  True,
            "notificacionVencimiento": True,
            "notificacionComentario":  True,
            "notificacionCambioEstado": True,
            "canal": "IN_APP",
        }
    return {
        "usuarioId":               prefs["usuarioId"],
        "notificacionAsignacion":  prefs.get("notificacionAsignacion", True),
        "notificacionVencimiento": prefs.get("notificacionVencimiento", True),
        "notificacionComentario":  prefs.get("notificacionComentario", True),
        "notificacionCambioEstado": prefs.get("notificacionCambioEstado", True),
        "canal": prefs.get("canal", "IN_APP"),
    }


async def actualizar_preferencias(usuario_id: str, datos: ActualizarPreferencias) -> dict:
    db = _db()
    cambios = {k: v for k, v in datos.model_dump().items() if v is not None}
    cambios["usuarioId"] = usuario_id
    await db["preferencias_notificacion"].update_one(
        {"usuarioId": usuario_id}, {"$set": cambios}, upsert=True
    )
    return await obtener_preferencias(usuario_id)


async def enviar_notificacion_externa(
    usuario_id: str,
    mensaje: str,
    canal: str = "email",
    asunto: str = "Notificación TaskFlow",
) -> dict:
    """
    Envía una notificación por canal externo usando Factory Method + Adapter.

    Flujo (igual que el ejemplo bancario):
      1. ProveedorNotificacion.get(canal)  → FabricaEmail / FabricaWhatsApp / FabricaSms
      2. fabrica.get()                     → EmailAdaptee / WhatsAppAdaptee / SmsAdaptee
      3. adapter.enviar(solicitud)         → llama a la API externa y traduce respuesta
    """
    db = _db()
    usuario = await db["usuarios"].find_one({"_id": usuario_id})
    if not usuario:
        return {"enviada": False, "detalle": "Usuario no encontrado"}

    try:
        # Paso 1 — Factory Method: obtener la fábrica del canal
        fabrica = _proveedor_notificacion.get(canal)

        # Paso 2 — Factory Method: crear el adaptador concreto
        adapter = fabrica.get()

        # Paso 3 — Adapter: traducir y enviar
        solicitud = SolicitudNotificacion(
            destinatario=usuario.get("nombre", "Usuario"),
            contacto=usuario.get("email", ""),
            mensaje=mensaje,
            asunto=asunto,
        )
        respuesta = adapter.enviar(solicitud)

        return {
            "enviada": respuesta.enviada,
            "canal":   respuesta.canal,
            "detalle": respuesta.detalle,
        }
    except ValueError as e:
        return {"enviada": False, "detalle": str(e)}
    except Exception as e:
        return {"enviada": False, "detalle": f"Error interno: {str(e)}"}