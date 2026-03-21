from datetime import datetime, timezone
from fastapi import HTTPException, status
import uuid

from app.db.conexion import ConexionMongoDB
from app.schemas.proyectos import CrearProyecto, ActualizarProyecto, InvitarMiembro
from app.patterns.prototype.clonadores import clonar_proyecto


def _db():
    return ConexionMongoDB.obtener_instancia().obtener_base_datos()


def _serializar(doc: dict) -> dict:
    return {
        "id": doc["_id"],
        "nombre": doc["nombre"],
        "descripcion": doc.get("descripcion"),
        "fechaInicio": doc["fechaInicio"],
        "fechaFinEstimada": doc["fechaFinEstimada"],
        "estado": doc["estado"],
        "propietarioId": doc["propietarioId"],
        "estaArchivado": doc.get("estaArchivado", False),
        "progreso": doc.get("progreso", 0.0),
        "miembros": doc.get("miembros", []),
        "creadoEn": doc["creadoEn"],
    }


async def _columnas_por_defecto(tablero_id: str) -> list[dict]:
    nombres = ["Por hacer", "En progreso", "En revisión", "Completado"]
    return [
        {
            "_id": str(uuid.uuid4()),
            "nombre": nombre,
            "tableroId": tablero_id,
            "posicion": i,
            "limiteWip": None,
        }
        for i, nombre in enumerate(nombres)
    ]


async def crear_proyecto(datos: CrearProyecto, propietario_id: str) -> dict:
    db = _db()
    ahora = datetime.now(timezone.utc)
    proyecto_id = str(uuid.uuid4())
    tablero_id = str(uuid.uuid4())

    # Todos los admins se agregan automáticamente como miembros para garantizar visibilidad global
    admins = [u["_id"] async for u in db["usuarios"].find({"rol": "ADMIN"})]
    miembros_iniciales = list(set([propietario_id] + admins))

    nuevo_proyecto = {
        "_id": proyecto_id,
        "nombre": datos.nombre,
        "descripcion": datos.descripcion,
        "fechaInicio": datos.fechaInicio.isoformat(),
        "fechaFinEstimada": datos.fechaFinEstimada.isoformat(),
        "estado": "PLANIFICADO",
        "propietarioId": propietario_id,
        "estaArchivado": False,
        "progreso": 0.0,
        "miembros": miembros_iniciales,
        "creadoEn": ahora,
        "actualizadoEn": ahora,
    }
    tablero_defecto = {
        "_id": tablero_id,
        "nombre": "Tablero principal",
        "proyectoId": proyecto_id,
        "esPorDefecto": True,
        "creadoEn": ahora,
    }
    columnas = await _columnas_por_defecto(tablero_id)

    await db["proyectos"].insert_one(nuevo_proyecto)
    await db["tableros"].insert_one(tablero_defecto)
    await db["columnas"].insert_many(columnas)
    return _serializar(nuevo_proyecto)


async def listar_proyectos(usuario_id: str, rol: str) -> list:
    db = _db()
    # ADMIN ve todos los proyectos; los demás solo los que son miembros
    if rol == "ADMIN":
        cursor = db["proyectos"].find({})
    else:
        cursor = db["proyectos"].find({"miembros": usuario_id})
    return [_serializar(p) async for p in cursor]


async def obtener_proyecto(proyecto_id: str, usuario_id: str, rol: str) -> dict:
    db = _db()
    proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if rol != "ADMIN" and usuario_id not in proyecto.get("miembros", []):
        raise HTTPException(status_code=403, detail="Sin acceso al proyecto")
    return _serializar(proyecto)


async def actualizar_proyecto(proyecto_id: str, datos: ActualizarProyecto, usuario_id: str, rol: str) -> dict:
    db = _db()
    proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if rol != "ADMIN" and proyecto["propietarioId"] != usuario_id:
        raise HTTPException(status_code=403, detail="Solo el propietario o un Admin puede editar el proyecto")
    if proyecto.get("estaArchivado"):
        raise HTTPException(status_code=400, detail="El proyecto está archivado y es de solo lectura")

    cambios = {k: v for k, v in datos.model_dump().items() if v is not None}
    if "fechaFinEstimada" in cambios:
        cambios["fechaFinEstimada"] = cambios["fechaFinEstimada"].isoformat()
    cambios["actualizadoEn"] = datetime.now(timezone.utc)
    await db["proyectos"].update_one({"_id": proyecto_id}, {"$set": cambios})
    return await obtener_proyecto(proyecto_id, usuario_id, rol)


async def eliminar_proyecto(proyecto_id: str, usuario_id: str, rol: str) -> dict:
    db = _db()
    proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if rol != "ADMIN" and proyecto["propietarioId"] != usuario_id:
        raise HTTPException(status_code=403, detail="Solo el propietario o un Admin puede eliminar el proyecto")
    await db["proyectos"].delete_one({"_id": proyecto_id})
    return {"mensaje": "Proyecto eliminado correctamente"}


async def archivar_proyecto(proyecto_id: str, usuario_id: str, rol: str) -> dict:
    db = _db()
    proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if rol != "ADMIN" and proyecto["propietarioId"] != usuario_id:
        raise HTTPException(status_code=403, detail="Solo el propietario o un Admin puede archivar el proyecto")
    await db["proyectos"].update_one(
        {"_id": proyecto_id},
        {"$set": {"estaArchivado": True, "estado": "ARCHIVADO", "actualizadoEn": datetime.now(timezone.utc)}},
    )
    return await obtener_proyecto(proyecto_id, usuario_id, rol)


async def invitar_miembro(proyecto_id: str, datos: InvitarMiembro, usuario_id: str, rol: str) -> dict:
    db = _db()
    proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if rol != "ADMIN" and usuario_id not in proyecto.get("miembros", []):
        raise HTTPException(status_code=403, detail="Sin acceso al proyecto")

    invitado = await db["usuarios"].find_one({"email": datos.email})
    if not invitado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado con ese correo")
    if invitado["_id"] in proyecto.get("miembros", []):
        raise HTTPException(status_code=400, detail="El usuario ya es miembro del proyecto")

    await db["proyectos"].update_one(
        {"_id": proyecto_id},
        {"$push": {"miembros": invitado["_id"]}},
    )
    return {"mensaje": f"Usuario {invitado['nombre']} invitado al proyecto"}


async def clonar_proyecto_servicio(proyecto_id: str, usuario_id: str, rol: str) -> dict:
    db = _db()
    proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    tableros = [t async for t in db["tableros"].find({"proyectoId": proyecto_id})]
    tablero_ids = [t["_id"] for t in tableros]
    columnas = [c async for c in db["columnas"].find({"tableroId": {"$in": tablero_ids}})]

    resultado = clonar_proyecto(proyecto, tableros, columnas, usuario_id)

    await db["proyectos"].insert_one(resultado["proyecto"])
    if resultado["tableros"]:
        await db["tableros"].insert_many(resultado["tableros"])
    if resultado["columnas"]:
        await db["columnas"].insert_many(resultado["columnas"])

    return _serializar(resultado["proyecto"])


async def obtener_miembros_proyecto(proyecto_id: str) -> list:
    db = _db()
    proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    miembro_ids = proyecto.get("miembros", [])
    cursor = db["usuarios"].find({"_id": {"$in": miembro_ids}}, {"passwordHash": 0})
    return [{"id": u["_id"], "nombre": u["nombre"], "email": u["email"], "rol": u["rol"]} async for u in cursor]