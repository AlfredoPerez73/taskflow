"""
Rutas de subtareas — CRUD completo + toggle completada.
Patrón Builder: la creación usa ConstructorSubtarea para construir
la subtarea paso a paso con validaciones fluidas.
"""
from fastapi import APIRouter, Depends
from app.services import servicio_subtarea
from app.core.dependencias import obtener_usuario_actual, requerir_rol

enrutador = APIRouter(tags=["Subtareas"])

_ROLES = ("DEVELOPER", "PROJECT_MANAGER", "ADMIN")


@enrutador.get(
    "/tareas/{tarea_id}/subtareas",
    summary="Listar subtareas de una tarea — Patrón Builder",
    description="Devuelve todas las subtareas de la tarea padre ordenadas por fecha de creación.",
)
async def listar_subtareas(
    tarea_id: str,
    _: dict = Depends(obtener_usuario_actual),
):
    return await servicio_subtarea.listar_subtareas(tarea_id)


@enrutador.post(
    "/tareas/{tarea_id}/subtareas",
    status_code=201,
    summary="Crear subtarea — Patrón Builder",
    description=(
        "**Patrón Builder:** Usa `ConstructorSubtarea` para construir la subtarea "
        "paso a paso (título → tarea → proyecto → responsables → fechaVencimiento). "
        "Campos: `titulo` (requerido), `descripcion`, `responsables`, `fechaVencimiento`."
    ),
)
async def crear_subtarea(
    tarea_id: str,
    body: dict,
    usuario: dict = Depends(requerir_rol(*_ROLES)),
):
    return await servicio_subtarea.crear_subtarea(tarea_id, body, usuario["_id"])


@enrutador.put(
    "/subtareas/{subtarea_id}",
    summary="Actualizar subtarea",
)
async def actualizar_subtarea(
    subtarea_id: str,
    body: dict,
    usuario: dict = Depends(requerir_rol(*_ROLES)),
):
    return await servicio_subtarea.actualizar_subtarea(subtarea_id, body, usuario["_id"])


@enrutador.delete(
    "/subtareas/{subtarea_id}",
    summary="Eliminar subtarea",
)
async def eliminar_subtarea(
    subtarea_id: str,
    usuario: dict = Depends(requerir_rol(*_ROLES)),
):
    return await servicio_subtarea.eliminar_subtarea(subtarea_id, usuario["_id"])


@enrutador.post(
    "/subtareas/{subtarea_id}/toggle",
    summary="Marcar/desmarcar subtarea como completada",
    description="Invierte el estado `completada` de la subtarea.",
)
async def toggle_subtarea(
    subtarea_id: str,
    usuario: dict = Depends(requerir_rol(*_ROLES)),
):
    return await servicio_subtarea.toggle_subtarea(subtarea_id, usuario["_id"])