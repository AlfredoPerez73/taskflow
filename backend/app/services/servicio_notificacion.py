"""
Servicio de notificaciones mejorado.
- Notificaciones internas (IN_APP) con SSE en tiempo real
- Envío externo por Email / WhatsApp / SMS via Adapter + Factory Method
- Preferencias por usuario: canal (IN_APP | EMAIL | AMBOS)
"""
from datetime import datetime, timezone
from fastapi import HTTPException
import uuid

from app.db.conexion import ConexionMongoDB
from app.schemas.notificaciones import ActualizarPreferencias
from app.patterns.adapter.notificacion_adapter import SolicitudNotificacion
from app.patterns.adapter.proveedor_notificacion import ProveedorNotificacion

# Instancia única del proveedor (reutilizable entre llamadas)
_proveedor_notificacion = ProveedorNotificacion()

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
        "id":          doc["_id"],
        "usuarioId":   doc["usuarioId"],
        "mensaje":     doc["mensaje"],
        "tipo":        doc["tipo"],
        "leida":       doc.get("leida", False),
        "creadoEn":    doc["creadoEn"],
        "tareaId":     doc.get("tareaId"),
        "proyectoId":  doc.get("proyectoId"),
        "tituloTarea": doc.get("tituloTarea"),
    }


# ─────────────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────────────

async def _obtener_preferencias_usuario(db, usuario_id: str) -> dict:
    """Devuelve las preferencias del usuario o los defaults."""
    prefs = await db["preferencias_notificacion"].find_one({"usuarioId": usuario_id})
    if not prefs:
        return {
            "usuarioId":               usuario_id,
            "notificacionAsignacion":  True,
            "notificacionVencimiento": True,
            "notificacionComentario":  True,
            "notificacionCambioEstado": True,
            "canal": "IN_APP",
            # Datos de contacto para canales externos (vacíos por defecto)
            "telefonoWhatsapp": None,
            "telefonoSms":      None,
        }
    return prefs


async def _enviar_por_canal_externo(
    db,
    usuario: dict,
    mensaje: str,
    canal: str,
    asunto: str = "Notificación TaskFlow",
) -> dict:
    """
    Envía por canal externo usando el patrón Adapter + Factory Method.
    Determina el contacto correcto según el canal:
      - email    → usuario["email"]
      - whatsapp → prefs["telefonoWhatsapp"] o usuario["telefono"]
      - sms      → prefs["telefonoSms"]      o usuario["telefono"]
    """
    # Obtener datos de contacto del canal
    prefs = await _obtener_preferencias_usuario(db, usuario["_id"])

    contacto_map = {
        "email":    usuario.get("email", ""),
        "whatsapp": prefs.get("telefonoWhatsapp") or usuario.get("telefono", ""),
        "sms":      prefs.get("telefonoSms")      or usuario.get("telefono", ""),
    }
    contacto = contacto_map.get(canal, usuario.get("email", ""))

    try:
        fabrica = _proveedor_notificacion.get(canal)
        adapter = fabrica.get()
        solicitud = SolicitudNotificacion(
            destinatario=usuario.get("nombre", "Usuario"),
            contacto=contacto,
            mensaje=mensaje,
            asunto=asunto,
        )
        respuesta = adapter.enviar(solicitud)
        return {
            "enviada": respuesta.enviada,
            "canal":   respuesta.canal,
            "detalle": respuesta.detalle,
            "contacto_usado": contacto,
        }
    except ValueError as e:
        return {"enviada": False, "canal": canal, "detalle": str(e)}
    except Exception as e:
        return {"enviada": False, "canal": canal, "detalle": f"Error: {str(e)}"}


# ─────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: crear notificación
# ─────────────────────────────────────────────────────

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
    Crea una notificación IN_APP y, según las preferencias del usuario,
    también envía por canal externo (email / whatsapp / sms).
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

    # Push SSE en tiempo real
    if _SSE_ACTIVO and gestor_eventos:
        gestor_eventos.publicar_a_usuario(usuario_id, evento_notificacion(notif))

    # Envío externo según preferencias
    try:
        prefs = await _obtener_preferencias_usuario(db, usuario_id)
        canal = prefs.get("canal", "IN_APP")

        # Verificar que el tipo de notificación está habilitado
        tipo_habilitado_map = {
            "TAREA_ASIGNADA":        prefs.get("notificacionAsignacion",   True),
            "TAREA_VENCIDA":         prefs.get("notificacionVencimiento",  True),
            "COMENTARIO_EN_TAREA":   prefs.get("notificacionComentario",   True),
            "MENCION_EN_COMENTARIO": prefs.get("notificacionComentario",   True),
            "ESTADO_TAREA_CAMBIADO": prefs.get("notificacionCambioEstado", True),
        }
        if not tipo_habilitado_map.get(tipo, True):
            return  # El usuario desactivó este tipo de notificación

        if canal in ("EMAIL", "AMBOS"):
            usuario = await db["usuarios"].find_one({"_id": usuario_id})
            if usuario:
                await _enviar_por_canal_externo(db, usuario, mensaje, "email")

        if canal == "AMBOS":
            usuario = usuario if "usuario" in dir() else await db["usuarios"].find_one({"_id": usuario_id})
            if usuario:
                tel = prefs.get("telefonoWhatsapp") or prefs.get("telefonoSms")
                if tel:
                    await _enviar_por_canal_externo(db, usuario, mensaje, "whatsapp")
    except Exception:
        pass  # Nunca bloquear el flujo principal por fallo en envío externo


# ─────────────────────────────────────────────────────
# CRUD NOTIFICACIONES
# ─────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────
# PREFERENCIAS
# ─────────────────────────────────────────────────────

async def obtener_preferencias(usuario_id: str) -> dict:
    db = _db()
    prefs = await db["preferencias_notificacion"].find_one({"usuarioId": usuario_id})
    base = {
        "usuarioId":               usuario_id,
        "notificacionAsignacion":  True,
        "notificacionVencimiento": True,
        "notificacionComentario":  True,
        "notificacionCambioEstado": True,
        "canal": "IN_APP",
        "telefonoWhatsapp": None,
        "telefonoSms":      None,
    }
    if prefs:
        base.update({k: v for k, v in prefs.items() if k != "_id"})
    return base


async def actualizar_preferencias(usuario_id: str, datos: ActualizarPreferencias) -> dict:
    db = _db()
    cambios = {k: v for k, v in datos.model_dump().items() if v is not None}
    cambios["usuarioId"] = usuario_id
    await db["preferencias_notificacion"].update_one(
        {"usuarioId": usuario_id}, {"$set": cambios}, upsert=True
    )
    return await obtener_preferencias(usuario_id)


async def actualizar_contacto_externo(
    usuario_id: str,
    telefono_whatsapp: str | None,
    telefono_sms: str | None,
) -> dict:
    """Guarda los datos de contacto para canales externos."""
    db = _db()
    cambios = {"usuarioId": usuario_id}
    if telefono_whatsapp is not None:
        cambios["telefonoWhatsapp"] = telefono_whatsapp
    if telefono_sms is not None:
        cambios["telefonoSms"] = telefono_sms
    await db["preferencias_notificacion"].update_one(
        {"usuarioId": usuario_id}, {"$set": cambios}, upsert=True
    )
    return await obtener_preferencias(usuario_id)


# ─────────────────────────────────────────────────────
# ENVÍO EXTERNO MANUAL (endpoint admin/PM)
# ─────────────────────────────────────────────────────

async def enviar_notificacion_externa(
    usuario_id: str,
    mensaje: str,
    canal: str = "email",
    asunto: str = "Notificación TaskFlow",
) -> dict:
    """
    Envía manualmente una notificación por canal externo.
    Usa Factory Method + Adapter exactamente como en el ejemplo bancario:
      1. ProveedorNotificacion.get(canal) → fábrica concreta
      2. fabrica.get()                    → adaptador concreto
      3. adapter.enviar(solicitud)        → API externa
    """
    db = _db()
    usuario = await db["usuarios"].find_one({"_id": usuario_id})
    if not usuario:
        return {"enviada": False, "canal": canal, "detalle": "Usuario no encontrado"}

    resultado = await _enviar_por_canal_externo(db, usuario, mensaje, canal, asunto)

    # Registrar también como notificación interna
    await crear_notificacion_interna(
        db, usuario_id,
        f"[{canal.upper()}] {mensaje}",
        "NOTIFICACION_EXTERNA",
    )

    return resultado


async def probar_canales(usuario_id: str, mensaje: str = "Prueba de canal TaskFlow") -> dict:
    """
    Prueba todos los canales disponibles para un usuario.
    Útil para verificar la configuración de contacto.
    """
    db = _db()
    usuario = await db["usuarios"].find_one({"_id": usuario_id})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    canales = _proveedor_notificacion.canales_disponibles()
    resultados = {}
    for canal in canales:
        resultados[canal] = await _enviar_por_canal_externo(
            db, usuario, mensaje, canal, f"Prueba TaskFlow — canal {canal}"
        )
    return {"usuarioId": usuario_id, "resultados": resultados}