from datetime import datetime, timezone
from fastapi import HTTPException
import uuid

from app.db.conexion import ConexionMongoDB
from app.schemas.tableros import CrearTablero, RenombrarTablero, CrearColumna, ActualizarColumna


def _db():
    return ConexionMongoDB.obtener_instancia().obtener_base_datos()


def _serializar_tablero(doc: dict, columnas: list) -> dict:
    return {
        "id": doc["_id"],
        "nombre": doc["nombre"],
        "proyectoId": doc["proyectoId"],
        "esPorDefecto": doc.get("esPorDefecto", False),
        "columnas": [_serializar_columna(c) for c in columnas],
        "creadoEn": doc["creadoEn"],
    }


def _serializar_columna(doc: dict) -> dict:
    return {
        "id": doc["_id"],
        "nombre": doc["nombre"],
        "tableroId": doc["tableroId"],
        "posicion": doc.get("posicion", 0),
        "limiteWip": doc.get("limiteWip"),
    }


async def listar_tableros(proyecto_id: str) -> list:
    db = _db()
    tableros = [t async for t in db["tableros"].find({"proyectoId": proyecto_id})]
    resultado = []
    for tablero in tableros:
        columnas = [c async for c in db["columnas"].find(
            {"tableroId": tablero["_id"]},
            sort=[("posicion", 1)]
        )]
        resultado.append(_serializar_tablero(tablero, columnas))
    return resultado


async def crear_tablero(datos: CrearTablero) -> dict:
    db = _db()
    ahora = datetime.now(timezone.utc)
    tablero_id = str(uuid.uuid4())
    nuevo = {
        "_id": tablero_id,
        "nombre": datos.nombre,
        "proyectoId": datos.proyectoId,
        "esPorDefecto": False,
        "creadoEn": ahora,
    }
    await db["tableros"].insert_one(nuevo)
    return _serializar_tablero(nuevo, [])


async def renombrar_tablero(tablero_id: str, datos: RenombrarTablero) -> dict:
    db = _db()
    tablero = await db["tableros"].find_one({"_id": tablero_id})
    if not tablero:
        raise HTTPException(status_code=404, detail="Tablero no encontrado")
    await db["tableros"].update_one({"_id": tablero_id}, {"$set": {"nombre": datos.nombre}})
    columnas = [c async for c in db["columnas"].find({"tableroId": tablero_id}, sort=[("posicion", 1)])]
    tablero["nombre"] = datos.nombre
    return _serializar_tablero(tablero, columnas)


async def eliminar_tablero(tablero_id: str) -> dict:
    db = _db()
    tablero = await db["tableros"].find_one({"_id": tablero_id})
    if not tablero:
        raise HTTPException(status_code=404, detail="Tablero no encontrado")
    if tablero.get("esPorDefecto"):
        raise HTTPException(status_code=400, detail="No se puede eliminar el tablero por defecto")
    await db["tableros"].delete_one({"_id": tablero_id})
    await db["columnas"].delete_many({"tableroId": tablero_id})
    return {"mensaje": "Tablero eliminado"}


async def crear_columna(tablero_id: str, datos: CrearColumna) -> dict:
    db = _db()
    tablero = await db["tableros"].find_one({"_id": tablero_id})
    if not tablero:
        raise HTTPException(status_code=404, detail="Tablero no encontrado")
    total = await db["columnas"].count_documents({"tableroId": tablero_id})
    nueva = {
        "_id": str(uuid.uuid4()),
        "nombre": datos.nombre,
        "tableroId": tablero_id,
        "posicion": total,
        "limiteWip": datos.limiteWip,
    }
    await db["columnas"].insert_one(nueva)
    return _serializar_columna(nueva)


async def actualizar_columna(columna_id: str, datos: ActualizarColumna) -> dict:
    db = _db()
    columna = await db["columnas"].find_one({"_id": columna_id})
    if not columna:
        raise HTTPException(status_code=404, detail="Columna no encontrada")
    cambios = {k: v for k, v in datos.model_dump().items() if v is not None}
    await db["columnas"].update_one({"_id": columna_id}, {"$set": cambios})
    columna.update(cambios)
    return _serializar_columna(columna)


async def eliminar_columna(columna_id: str) -> dict:
    db = _db()
    columna = await db["columnas"].find_one({"_id": columna_id})
    if not columna:
        raise HTTPException(status_code=404, detail="Columna no encontrada")
    hay_tareas = await db["tareas"].count_documents({"columnaId": columna_id})
    if hay_tareas:
        raise HTTPException(status_code=400, detail="La columna tiene tareas. Muévalas antes de eliminarla")
    await db["columnas"].delete_one({"_id": columna_id})
    return {"mensaje": "Columna eliminada"}