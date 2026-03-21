from fastapi import APIRouter, Depends
from app.schemas.tableros import CrearTablero, RenombrarTablero, CrearColumna, ActualizarColumna
from app.services import servicio_tablero
from app.core.dependencias import obtener_usuario_actual

enrutador = APIRouter(tags=["Tableros"])


@enrutador.get("/proyectos/{proyecto_id}/tableros")
async def listar_tableros(
    proyecto_id: str,
    _: dict = Depends(obtener_usuario_actual),
):
    return await servicio_tablero.listar_tableros(proyecto_id)


@enrutador.post("/tableros", status_code=201)
async def crear_tablero(
    datos: CrearTablero,
    _: dict = Depends(obtener_usuario_actual),
):
    return await servicio_tablero.crear_tablero(datos)


@enrutador.put("/tableros/{tablero_id}")
async def renombrar_tablero(
    tablero_id: str,
    datos: RenombrarTablero,
    _: dict = Depends(obtener_usuario_actual),
):
    return await servicio_tablero.renombrar_tablero(tablero_id, datos)


@enrutador.delete("/tableros/{tablero_id}")
async def eliminar_tablero(
    tablero_id: str,
    _: dict = Depends(obtener_usuario_actual),
):
    return await servicio_tablero.eliminar_tablero(tablero_id)


@enrutador.post("/tableros/{tablero_id}/columnas", status_code=201)
async def crear_columna(
    tablero_id: str,
    datos: CrearColumna,
    _: dict = Depends(obtener_usuario_actual),
):
    return await servicio_tablero.crear_columna(tablero_id, datos)


@enrutador.put("/columnas/{columna_id}")
async def actualizar_columna(
    columna_id: str,
    datos: ActualizarColumna,
    _: dict = Depends(obtener_usuario_actual),
):
    return await servicio_tablero.actualizar_columna(columna_id, datos)


@enrutador.delete("/columnas/{columna_id}")
async def eliminar_columna(
    columna_id: str,
    _: dict = Depends(obtener_usuario_actual),
):
    return await servicio_tablero.eliminar_columna(columna_id)