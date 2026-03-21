from datetime import datetime, timezone
from fastapi import HTTPException
import uuid

from app.db.conexion import ConexionMongoDB
from app.schemas.tareas import (
    CrearTarea, ActualizarTarea, MoverTarea,
    CrearComentario, ActualizarComentario, RegistrarTiempo, CrearEtiqueta,
)
from app.patterns.factory.fabrica_tareas import obtener_creador
from app.patterns.builder.constructores_tareas import ConstructorTareaAvanzada
from app.patterns.prototype.clonadores import clonar_tarea
from app.services.servicio_notificacion import crear_notificacion_interna
from app.services.servicio_mencion import extraer_y_notificar_menciones, resaltar_menciones


def _db():
    return ConexionMongoDB.obtener_instancia().obtener_base_datos()


def _serializar(doc: dict) -> dict:
    return {
        "id": doc["_id"],
        "titulo": doc["titulo"],
        "descripcion": doc.get("descripcion"),
        "prioridad": doc["prioridad"],
        "tipo": doc["tipo"],
        "fechaVencimiento": doc.get("fechaVencimiento"),
        "horasEstimadas": doc.get("horasEstimadas"),
        "columnaId": doc["columnaId"],
        "proyectoId": doc["proyectoId"],
        "responsables": doc.get("responsables", []),
        "etiquetas": doc.get("etiquetas", []),
        "estaVencida": doc.get("estaVencida", False),
        "subtareas": doc.get("subtareas", []),
        "horasRegistradas": doc.get("horasRegistradas", 0.0),
        "creadoEn": doc["creadoEn"],
    }


async def crear_tarea(datos: CrearTarea, usuario_id: str) -> dict:
    """Usa el patrón Factory Method para instanciar la tarea según su tipo."""
    db = _db()
    creador = obtener_creador(datos.tipo.value)
    nueva_tarea = creador.crear(
        titulo=datos.titulo,
        columna_id=datos.columnaId,
        proyecto_id=datos.proyectoId,
        creado_por=usuario_id,
        descripcion=datos.descripcion,
        responsables=datos.responsables,
        fecha_vencimiento=datos.fechaVencimiento,
        horas_estimadas=datos.horasEstimadas,
        etiquetas=datos.etiquetas,
    )
    await db["tareas"].insert_one(nueva_tarea)
    await _registrar_auditoria(db, "tarea", nueva_tarea["_id"], "CREADA", usuario_id, None, nueva_tarea, datos.proyectoId)
    for responsable_id in datos.responsables:
        await crear_notificacion_interna(db, responsable_id, f"Se te ha asignado la tarea: {datos.titulo}", "TAREA_ASIGNADA", tarea_id=nueva_tarea["_id"], proyecto_id=datos.proyectoId, titulo_tarea=datos.titulo)
    return _serializar(nueva_tarea)


async def crear_tarea_avanzada(datos: dict, usuario_id: str) -> dict:
    """Usa el patrón Builder para construir una tarea con configuración detallada."""
    db = _db()
    from app.models.enums import TipoTarea, PrioridadTarea
    constructor = ConstructorTareaAvanzada()
    tarea = (
        constructor
        .con_titulo(datos["titulo"])
        .con_descripcion(datos.get("descripcion"))
        .con_tipo(TipoTarea(datos.get("tipo", "TASK")))
        .con_prioridad(PrioridadTarea(datos.get("prioridad", "MEDIA")))
        .en_columna(datos["columnaId"])
        .en_proyecto(datos["proyectoId"])
        .creado_por(usuario_id)
        .con_responsables(datos.get("responsables", []))
        .con_etiquetas(datos.get("etiquetas", []))
        .con_subtareas(datos.get("subtareas", []))
        .con_metadatos(datos.get("metadatos", {}))
    )
    if datos.get("fechaVencimiento"):
        tarea = tarea.con_fecha_vencimiento(datos["fechaVencimiento"])
    if datos.get("horasEstimadas"):
        tarea = tarea.con_horas_estimadas(datos["horasEstimadas"])
    nueva_tarea = tarea.construir()
    await db["tareas"].insert_one(nueva_tarea)
    return _serializar(nueva_tarea)


async def listar_tareas_columna(columna_id: str, usuario_id: str, rol: str) -> list:
    db = _db()
    if rol == "ADMIN":
        cursor = db["tareas"].find({"columnaId": columna_id})
    else:
        proyecto_ids = [p["_id"] async for p in db["proyectos"].find({"miembros": usuario_id})]
        cursor = db["tareas"].find({"columnaId": columna_id, "proyectoId": {"$in": proyecto_ids}})
    return [_serializar(t) async for t in cursor]


async def listar_tareas_proyecto(
    proyecto_id: str,
    usuario_id: str,
    rol: str,
    filtros: dict | None = None,
    pagina: int = 1,
    limite: int = 50,
) -> dict:
    """Devuelve tareas paginadas del proyecto con filtros opcionales."""
    db = _db()
    if rol != "ADMIN":
        proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
        if not proyecto or usuario_id not in proyecto.get("miembros", []):
            raise HTTPException(status_code=403, detail="Sin acceso al proyecto")

    query: dict = {"proyectoId": proyecto_id}
    if filtros:
        if filtros.get("texto"):
            query["$text"] = {"$search": filtros["texto"]}
        if filtros.get("responsableId"):
            query["responsables"] = filtros["responsableId"]
        if filtros.get("etiqueta"):
            query["etiquetas"] = filtros["etiqueta"]
        if filtros.get("prioridad"):
            query["prioridad"] = filtros["prioridad"]
        if filtros.get("tipo"):
            query["tipo"] = filtros["tipo"]

    total = await db["tareas"].count_documents(query)
    skip = (pagina - 1) * limite
    cursor = db["tareas"].find(query).skip(skip).limit(limite)
    datos = [_serializar(t) async for t in cursor]
    total_paginas = (total + limite - 1) // limite if total > 0 else 1

    return {
        "datos": datos,
        "pagina": pagina,
        "limite": limite,
        "total": total,
        "totalPaginas": total_paginas,
        "tieneSiguiente": pagina < total_paginas,
        "tieneAnterior": pagina > 1,
    }


async def obtener_tarea(tarea_id: str) -> dict:
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return _serializar(tarea)


async def actualizar_tarea(tarea_id: str, datos: ActualizarTarea, usuario_id: str) -> dict:
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cambios = {k: v for k, v in datos.model_dump().items() if v is not None}
    cambios["actualizadoEn"] = datetime.now(timezone.utc)

    responsables_nuevos = cambios.get("responsables", [])
    responsables_anteriores = tarea.get("responsables", [])
    nuevos_asignados = [r for r in responsables_nuevos if r not in responsables_anteriores]

    await db["tareas"].update_one({"_id": tarea_id}, {"$set": cambios})
    await _registrar_auditoria(db, "tarea", tarea_id, "ACTUALIZADA", usuario_id, tarea, cambios, tarea["proyectoId"])

    for responsable_id in nuevos_asignados:
        await crear_notificacion_interna(db, responsable_id, f"Se te ha asignado la tarea: {tarea['titulo']}", "TAREA_ASIGNADA", tarea_id=tarea_id, proyecto_id=tarea["proyectoId"], titulo_tarea=tarea["titulo"])
    return await obtener_tarea(tarea_id)


async def asignar_responsables(tarea_id: str, responsables: list[str], usuario_id: str) -> dict:
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    anteriores = tarea.get("responsables", [])
    nuevos = [r for r in responsables if r not in anteriores]
    await db["tareas"].update_one(
        {"_id": tarea_id},
        {"$set": {"responsables": responsables, "actualizadoEn": datetime.now(timezone.utc)}},
    )
    for r_id in nuevos:
        await crear_notificacion_interna(db, r_id, f"Se te ha asignado la tarea: {tarea['titulo']}", "TAREA_ASIGNADA", tarea_id=tarea_id, proyecto_id=tarea["proyectoId"], titulo_tarea=tarea["titulo"])
    return await obtener_tarea(tarea_id)


async def mover_tarea(tarea_id: str, datos: MoverTarea, usuario_id: str) -> dict:
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    columna_destino = await db["columnas"].find_one({"_id": datos.columnaIdDestino})
    if not columna_destino:
        raise HTTPException(status_code=404, detail="Columna destino no encontrada")
    if columna_destino.get("limiteWip"):
        tareas_en_columna = await db["tareas"].count_documents({"columnaId": datos.columnaIdDestino})
        if tareas_en_columna >= columna_destino["limiteWip"]:
            raise HTTPException(status_code=400, detail=f"Límite WIP alcanzado en '{columna_destino['nombre']}'")
    columna_anterior = tarea["columnaId"]
    await db["tareas"].update_one(
        {"_id": tarea_id},
        {"$set": {"columnaId": datos.columnaIdDestino, "actualizadoEn": datetime.now(timezone.utc)}},
    )
    await _registrar_auditoria(db, "tarea", tarea_id, "MOVIDA", usuario_id,
                               {"columnaId": columna_anterior}, {"columnaId": datos.columnaIdDestino},
                               tarea["proyectoId"])
    for r_id in tarea.get("responsables", []):
        await crear_notificacion_interna(db, r_id, f"La tarea '{tarea["titulo"]}' fue movida", "ESTADO_TAREA_CAMBIADO", tarea_id=tarea_id, proyecto_id=tarea["proyectoId"], titulo_tarea=tarea["titulo"])
    return await obtener_tarea(tarea_id)


async def clonar_tarea_servicio(tarea_id: str, usuario_id: str) -> dict:
    """Usa el patrón Prototype para clonar la tarea."""
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    clon = clonar_tarea(tarea)
    await db["tareas"].insert_one(clon)
    return _serializar(clon)


async def eliminar_tarea(tarea_id: str, usuario_id: str) -> dict:
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    await db["tareas"].delete_one({"_id": tarea_id})
    await db["comentarios"].delete_many({"tareaId": tarea_id})
    await _registrar_auditoria(db, "tarea", tarea_id, "ELIMINADA", usuario_id, tarea, None, tarea["proyectoId"])
    return {"mensaje": "Tarea eliminada"}


async def agregar_comentario(tarea_id: str, datos: CrearComentario, usuario_id: str) -> dict:
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    ahora = datetime.now(timezone.utc)

    # Procesar menciones @usuario
    mencionados = await extraer_y_notificar_menciones(
        db, datos.contenido, usuario_id, tarea["titulo"], tarea["proyectoId"], tarea_id=tarea_id
    )

    comentario = {
        "_id": str(uuid.uuid4()),
        "contenido": datos.contenido,
        "contenidoHtml": resaltar_menciones(datos.contenido),
        "tareaId": tarea_id,
        "autorId": usuario_id,
        "mencionados": mencionados,
        "creadoEn": ahora,
        "actualizadoEn": ahora,
    }
    await db["comentarios"].insert_one(comentario)

    # Notificar a responsables (excepto al autor y ya mencionados)
    for r_id in tarea.get("responsables", []):
        if r_id != usuario_id and r_id not in mencionados:
            await crear_notificacion_interna(db, r_id, f"Nuevo comentario en '{tarea["titulo"]}'", "COMENTARIO_EN_TAREA", tarea_id=tarea_id, proyecto_id=tarea["proyectoId"], titulo_tarea=tarea["titulo"])

    return _serializar_comentario(comentario)


async def listar_comentarios(tarea_id: str, pagina: int = 1, limite: int = 30) -> dict:
    db = _db()
    total = await db["comentarios"].count_documents({"tareaId": tarea_id})
    skip = (pagina - 1) * limite
    cursor = db["comentarios"].find({"tareaId": tarea_id}, sort=[("creadoEn", 1)]).skip(skip).limit(limite)
    datos = [_serializar_comentario(c) async for c in cursor]
    total_paginas = (total + limite - 1) // limite if total > 0 else 1
    return {
        "datos": datos,
        "pagina": pagina,
        "limite": limite,
        "total": total,
        "totalPaginas": total_paginas,
        "tieneSiguiente": pagina < total_paginas,
        "tieneAnterior": pagina > 1,
    }


def _serializar_comentario(c: dict) -> dict:
    return {
        "id": c["_id"],
        "contenido": c["contenido"],
        "contenidoHtml": c.get("contenidoHtml", c["contenido"]),
        "tareaId": c["tareaId"],
        "autorId": c["autorId"],
        "mencionados": c.get("mencionados", []),
        "creadoEn": c["creadoEn"],
        "actualizadoEn": c["actualizadoEn"],
    }


async def actualizar_comentario(comentario_id: str, datos: ActualizarComentario, usuario_id: str) -> dict:
    db = _db()
    comentario = await db["comentarios"].find_one({"_id": comentario_id})
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    if comentario["autorId"] != usuario_id:
        raise HTTPException(status_code=403, detail="Solo el autor puede editar el comentario")
    ahora = datetime.now(timezone.utc)
    await db["comentarios"].update_one(
        {"_id": comentario_id},
        {"$set": {
            "contenido": datos.contenido,
            "contenidoHtml": resaltar_menciones(datos.contenido),
            "actualizadoEn": ahora,
        }}
    )
    comentario.update({"contenido": datos.contenido, "actualizadoEn": ahora})
    return _serializar_comentario(comentario)


async def eliminar_comentario(comentario_id: str, usuario_id: str) -> dict:
    db = _db()
    comentario = await db["comentarios"].find_one({"_id": comentario_id})
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    if comentario["autorId"] != usuario_id:
        raise HTTPException(status_code=403, detail="Solo el autor puede eliminar el comentario")
    await db["comentarios"].delete_one({"_id": comentario_id})
    return {"mensaje": "Comentario eliminado"}


async def registrar_tiempo(tarea_id: str, datos: RegistrarTiempo, usuario_id: str) -> dict:
    db = _db()
    tarea = await db["tareas"].find_one({"_id": tarea_id})
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    registro = {"_id": str(uuid.uuid4()), "tareaId": tarea_id, "usuarioId": usuario_id,
                "horas": datos.horas, "registradoEn": datetime.now(timezone.utc)}
    await db["registros_tiempo"].insert_one(registro)
    await db["tareas"].update_one({"_id": tarea_id}, {"$inc": {"horasRegistradas": datos.horas}})
    return {"mensaje": f"{datos.horas} horas registradas correctamente"}


async def crear_etiqueta(datos: CrearEtiqueta, usuario_id: str) -> dict:
    db = _db()
    etiqueta = {"_id": str(uuid.uuid4()), "nombre": datos.nombre, "color": datos.color, "proyectoId": datos.proyectoId}
    await db["etiquetas"].insert_one(etiqueta)
    return {"id": etiqueta["_id"], "nombre": etiqueta["nombre"], "color": etiqueta["color"], "proyectoId": etiqueta["proyectoId"]}


async def listar_etiquetas(proyecto_id: str) -> list:
    db = _db()
    cursor = db["etiquetas"].find({"proyectoId": proyecto_id})
    return [{"id": e["_id"], "nombre": e["nombre"], "color": e["color"]} async for e in cursor]


async def _registrar_auditoria(db, tipo_entidad, entidad_id, accion, usuario_id, valor_anterior, valor_nuevo, proyecto_id):
    await db["registros_auditoria"].insert_one({
        "_id": str(uuid.uuid4()), "tipoEntidad": tipo_entidad, "entidadId": entidad_id,
        "accion": accion, "usuarioId": usuario_id, "valorAnterior": valor_anterior,
        "valorNuevo": valor_nuevo, "proyectoId": proyecto_id, "marca": datetime.now(timezone.utc),
    })