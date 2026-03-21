from fastapi import APIRouter, Depends
from typing import List
from app.schemas.tableros import CrearTablero, RenombrarTablero, CrearColumna, ActualizarColumna, RespuestaTablero, RespuestaColumna
from app.services import servicio_tablero
from app.core.dependencias import obtener_usuario_actual, requerir_rol

enrutador = APIRouter(tags=["Tableros"])


@enrutador.get("/proyectos/{proyecto_id}/tableros", response_model=List[RespuestaTablero],
    summary="Listar tableros del proyecto",
    description="Devuelve todos los tableros con sus columnas anidadas. Visible para todos los miembros del proyecto.")
async def listar_tableros(proyecto_id: str, _: dict = Depends(obtener_usuario_actual)):
    return await servicio_tablero.listar_tableros(proyecto_id)


@enrutador.post("/tableros", status_code=201, response_model=RespuestaTablero,
    summary="Crear tablero adicional",
    description="Crea un tablero extra en el proyecto. El tablero por defecto se crea automáticamente al crear el proyecto. **PM y ADMIN.**")
async def crear_tablero(datos: CrearTablero, _: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_tablero.crear_tablero(datos)


@enrutador.put("/tableros/{tablero_id}", response_model=RespuestaTablero,
    summary="Renombrar tablero",
    description="Cambia el nombre de un tablero existente. **PM y ADMIN.**")
async def renombrar_tablero(tablero_id: str, datos: RenombrarTablero, _: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_tablero.renombrar_tablero(tablero_id, datos)


@enrutador.delete("/tableros/{tablero_id}",
    summary="Eliminar tablero",
    description="Elimina el tablero y todas sus columnas. No se puede eliminar el tablero marcado como `esPorDefecto`. **PM y ADMIN.**")
async def eliminar_tablero(tablero_id: str, _: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_tablero.eliminar_tablero(tablero_id)


@enrutador.post("/tableros/{tablero_id}/columnas", status_code=201, response_model=RespuestaColumna,
    summary="Crear columna en tablero",
    description="Agrega una columna al tablero. Se puede configurar un límite WIP (Work In Progress). **PM y ADMIN.**")
async def crear_columna(tablero_id: str, datos: CrearColumna, _: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_tablero.crear_columna(tablero_id, datos)


@enrutador.put("/columnas/{columna_id}", response_model=RespuestaColumna,
    summary="Actualizar columna",
    description="Modifica el nombre, posición o límite WIP de una columna. **PM y ADMIN.**")
async def actualizar_columna(columna_id: str, datos: ActualizarColumna, _: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_tablero.actualizar_columna(columna_id, datos)


@enrutador.delete("/columnas/{columna_id}",
    summary="Eliminar columna",
    description="Elimina la columna. La columna debe estar **vacía** (sin tareas) para poder eliminarla. **PM y ADMIN.**")
async def eliminar_columna(columna_id: str, _: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_tablero.eliminar_columna(columna_id)