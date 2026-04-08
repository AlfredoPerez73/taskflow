"""
Servicio de subtareas — gestión de tareas hijas dentro de una tarea padre.
Las subtareas se almacenan en la colección 'subtareas' con referencia a tareaId.
"""
from datetime import datetime, timezone
from fastapi import HTTPException
import uuid

from app.db.conexion import ConexionMongoDB
from app.schemas.tareas import CrearSubtarea, ActualizarSubtarea
from app.patterns.builder.constructor_subtarea import ConstructorSubtarea

# Builder reutilizable para construir subtareas paso a paso
_constructor_subtarea = ConstructorSubtarea()


def _db():
    return ConexionMongoDB.obtener_instancia().obtener_base_datos()


def _fmt(s: dict) -> dict:
    return {
        "id":               s["_id"],
        "titulo":           s["titulo"],
        "descripcion":      s.get("descripcion"),
        "completada":       s.get("completada", False),
        "tareaId":          s["tareaId"],
        "proyectoId":       s["proyectoId"],
        "responsables":     s.get("responsables", []),
        "fechaVencimiento": s.get("fechaVencimiento"),
        "creadoEn":         s["creadoEn"],
    }


async def listar_subtareas(tarea_id: str) -> list:
    db = _db()
    # Verificar que la tarea existe
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cursor = db["subtareas"].find({"tareaId": tarea_id}, sort=[("creadoEn", 1)])
    return [_fmt(s) async for s in cursor]


async def crear_subtarea(tarea_id: str, datos: CrearSubtarea, usuario_id: str) -> dict:
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # Usar el patrón Builder para construir la subtarea paso a paso
    constructor = (
        _constructor_subtarea
        .con_titulo(datos.titulo)
        .en_tarea(tarea_id)
        .en_proyecto(tarea["proyectoId"])
        .creada_por(usuario_id)
        .con_responsables(datos.responsables)
    )
    if datos.descripcion:
        constructor = constructor.con_descripcion(datos.descripcion)
    if datos.fechaVencimiento:
        constructor = constructor.con_fecha_vencimiento(datos.fechaVencimiento)

    subtarea = constructor.construir()
    await db["subtareas"].insert_one(subtarea)

    # Actualizar contador en la tarea padre
    await db["tareas"].update_one(
        {"_id": tarea_id},
        {"$addToSet": {"subtareas": subtarea["_id"]}}
    )

    # Registrar en auditoría
    await db["registros_auditoria"].insert_one({
        "_id":         str(uuid.uuid4()),
        "tipoEntidad": "subtarea",
        "entidadId":   subtarea["_id"],
        "accion":      "CREADA",
        "usuarioId":   usuario_id,
        "proyectoId":  tarea["proyectoId"],
        "valorAnterior": None,
        "valorNuevo":  {"titulo": datos.titulo},
        "marca":       ahora,
    })

    return _fmt(subtarea)


async def actualizar_subtarea(subtarea_id: str, datos: ActualizarSubtarea, usuario_id: str) -> dict:
    db = _db()
    subtarea = await db["subtareas"].find_one({"_id": subtarea_id})
    if not subtarea:
        raise HTTPException(status_code=404, detail="Subtarea no encontrada")

    cambios = {k: v for k, v in datos.model_dump().items() if v is not None}
    cambios["actualizadoEn"] = datetime.now(timezone.utc)

    await db["subtareas"].update_one({"_id": subtarea_id}, {"$set": cambios})
    actualizada = await db["subtareas"].find_one({"_id": subtarea_id})
    return _fmt(actualizada)


async def eliminar_subtarea(subtarea_id: str, usuario_id: str) -> dict:
    db = _db()
    subtarea = await db["subtareas"].find_one({"_id": subtarea_id})
    if not subtarea:
        raise HTTPException(status_code=404, detail="Subtarea no encontrada")

    await db["subtareas"].delete_one({"_id": subtarea_id})

    # Quitar referencia en la tarea padre
    await db["tareas"].update_one(
        {"_id": subtarea["tareaId"]},
        {"$pull": {"subtareas": subtarea_id}}
    )

    return {"mensaje": "Subtarea eliminada"}


async def toggle_subtarea(subtarea_id: str, usuario_id: str) -> dict:
    """Marcar/desmarcar subtarea como completada."""
    db = _db()
    subtarea = await db["subtareas"].find_one({"_id": subtarea_id})
    if not subtarea:
        raise HTTPException(status_code=404, detail="Subtarea no encontrada")

    nuevo_estado = not subtarea.get("completada", False)
    await db["subtareas"].update_one(
        {"_id": subtarea_id},
        {"$set": {"completada": nuevo_estado, "actualizadoEn": datetime.now(timezone.utc)}}
    )
    actualizada = await db["subtareas"].find_one({"_id": subtarea_id})
    return _fmt(actualizada)