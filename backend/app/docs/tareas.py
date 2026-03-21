from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from app.schemas.tareas import (
    CrearTarea, ActualizarTarea, MoverTarea,
    CrearComentario, ActualizarComentario, RegistrarTiempo,
    CrearEtiqueta, RespuestaTarea, RespuestaComentario,
)
from app.services import servicio_tarea
from app.core.dependencias import obtener_usuario_actual, requerir_rol

enrutador = APIRouter(tags=["Tareas"])

_ROLES_TAREA = ("DEVELOPER", "PROJECT_MANAGER", "ADMIN")


@enrutador.post("/tareas", status_code=201, response_model=RespuestaTarea,
    summary="Crear tarea — Patrón Factory Method",
    description="**Patrón Factory Method:** Según el campo `tipo` se instancia un creador diferente que inyecta metadatos automáticamente:\n- `BUG` → CreadorBug (severidad: alta, requiereReproduccion: true)\n- `FEATURE` → CreadorFeature (requiereRevisionDiseno: true)\n- `TASK` → CreadorTaskGeneral\n- `IMPROVEMENT` → CreadorMejora (afectaRendimiento: true)\n\n**DEV, PM y ADMIN.**")
async def crear_tarea(datos: CrearTarea, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.crear_tarea(datos, usuario["_id"])


@enrutador.post("/tareas/avanzada", status_code=201, response_model=RespuestaTarea,
    summary="Crear tarea avanzada — Patrón Builder",
    description="**Patrón Builder:** Construye la tarea paso a paso usando `ConstructorTareaAvanzada`. Permite configurar subtareas, metadatos personalizados y todos los atributos de forma fluida. **DEV, PM y ADMIN.**")
async def crear_tarea_avanzada(datos: dict, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.crear_tarea_avanzada(datos, usuario["_id"])


@enrutador.get("/columnas/{columna_id}/tareas", response_model=List[RespuestaTarea],
    summary="Listar tareas de una columna",
    description="Devuelve todas las tareas de la columna. ADMIN ve todas; DEV y PM ven solo las de sus proyectos.")
async def listar_tareas_columna(columna_id: str, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_tarea.listar_tareas_columna(columna_id, usuario["_id"], usuario["rol"])


@enrutador.get("/proyectos/{proyecto_id}/tareas", response_model=List[RespuestaTarea],
    summary="Listar y filtrar tareas del proyecto",
    description="Devuelve las tareas del proyecto con soporte de filtros opcionales por texto, responsable, etiqueta, prioridad y tipo.")
async def listar_tareas_proyecto(
    proyecto_id: str,
    texto: Optional[str] = Query(None, description="Busca en título y descripción"),
    responsable_id: Optional[str] = Query(None, description="UUID del responsable"),
    etiqueta: Optional[str] = Query(None, description="Nombre de la etiqueta"),
    prioridad: Optional[str] = Query(None, description="BAJA | MEDIA | ALTA | URGENTE"),
    tipo: Optional[str] = Query(None, description="BUG | FEATURE | TASK | IMPROVEMENT"),
    usuario: dict = Depends(obtener_usuario_actual),
):
    filtros = {k: v for k, v in {"texto": texto, "responsableId": responsable_id, "etiqueta": etiqueta, "prioridad": prioridad, "tipo": tipo}.items() if v}
    return await servicio_tarea.listar_tareas_proyecto(proyecto_id, usuario["_id"], usuario["rol"], filtros or None)


@enrutador.get("/tareas/{tarea_id}", response_model=RespuestaTarea,
    summary="Obtener tarea por ID",
    description="Devuelve todos los datos de una tarea incluyendo responsables, etiquetas y subtareas.")
async def obtener_tarea(tarea_id: str, _: dict = Depends(obtener_usuario_actual)):
    return await servicio_tarea.obtener_tarea(tarea_id)


@enrutador.put("/tareas/{tarea_id}", response_model=RespuestaTarea,
    summary="Actualizar tarea",
    description="Actualiza los campos enviados. Los cambios quedan registrados en el log de auditoría. **DEV, PM y ADMIN.**")
async def actualizar_tarea(tarea_id: str, datos: ActualizarTarea, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.actualizar_tarea(tarea_id, datos, usuario["_id"])


@enrutador.put("/tareas/{tarea_id}/responsables", response_model=RespuestaTarea,
    summary="Asignar responsables a tarea",
    description="Reemplaza la lista completa de responsables. Envía notificación automática a los nuevos asignados. **DEV, PM y ADMIN.**")
async def asignar_responsables(tarea_id: str, cuerpo: dict, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.asignar_responsables(tarea_id, cuerpo.get("responsables", []), usuario["_id"])


@enrutador.post("/tareas/{tarea_id}/mover", response_model=RespuestaTarea,
    summary="Mover tarea entre columnas",
    description="Mueve la tarea a otra columna. Verifica el límite WIP de la columna destino. Registra el movimiento en auditoría y notifica a los responsables. **DEV, PM y ADMIN.**")
async def mover_tarea(tarea_id: str, datos: MoverTarea, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.mover_tarea(tarea_id, datos, usuario["_id"])


@enrutador.post("/tareas/{tarea_id}/clonar", status_code=201, response_model=RespuestaTarea,
    summary="Clonar tarea — Patrón Prototype",
    description="**Patrón Prototype:** Crea una copia profunda de la tarea con nuevo UUID, prefijo `[Copia]` en el título y `horasRegistradas` reseteadas a 0. **DEV, PM y ADMIN.**")
async def clonar_tarea(tarea_id: str, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.clonar_tarea_servicio(tarea_id, usuario["_id"])


@enrutador.delete("/tareas/{tarea_id}",
    summary="Eliminar tarea",
    description="Elimina la tarea y todos sus comentarios. El evento queda registrado en auditoría. **DEV, PM y ADMIN.**")
async def eliminar_tarea(tarea_id: str, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.eliminar_tarea(tarea_id, usuario["_id"])


@enrutador.get("/tareas/{tarea_id}/comentarios", response_model=List[RespuestaComentario],
    summary="Listar comentarios de una tarea",
    description="Devuelve los comentarios ordenados cronológicamente.")
async def listar_comentarios(tarea_id: str, _: dict = Depends(obtener_usuario_actual)):
    return await servicio_tarea.listar_comentarios(tarea_id)


@enrutador.post("/tareas/{tarea_id}/comentarios", status_code=201, response_model=RespuestaComentario,
    summary="Agregar comentario a tarea",
    description="Agrega un comentario. Notifica automáticamente a los responsables de la tarea (excepto al autor). **DEV, PM y ADMIN.**")
async def agregar_comentario(tarea_id: str, datos: CrearComentario, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.agregar_comentario(tarea_id, datos, usuario["_id"])


@enrutador.put("/comentarios/{comentario_id}", response_model=RespuestaComentario,
    summary="Editar comentario",
    description="Solo el **autor** del comentario puede editarlo. **DEV, PM y ADMIN.**")
async def actualizar_comentario(comentario_id: str, datos: ActualizarComentario, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.actualizar_comentario(comentario_id, datos, usuario["_id"])


@enrutador.delete("/comentarios/{comentario_id}",
    summary="Eliminar comentario",
    description="Solo el **autor** del comentario puede eliminarlo. **DEV, PM y ADMIN.**")
async def eliminar_comentario(comentario_id: str, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.eliminar_comentario(comentario_id, usuario["_id"])


@enrutador.post("/tareas/{tarea_id}/tiempo",
    summary="Registrar horas trabajadas en tarea",
    description="Acumula horas al campo `horasRegistradas` de la tarea. **DEV, PM y ADMIN.**")
async def registrar_tiempo(tarea_id: str, datos: RegistrarTiempo, usuario: dict = Depends(requerir_rol(*_ROLES_TAREA))):
    return await servicio_tarea.registrar_tiempo(tarea_id, datos, usuario["_id"])


@enrutador.post("/etiquetas", status_code=201,
    summary="Crear etiqueta de proyecto",
    description="Crea una etiqueta con color personalizado reutilizable dentro del proyecto. **PM y ADMIN.**")
async def crear_etiqueta(datos: CrearEtiqueta, usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_tarea.crear_etiqueta(datos, usuario["_id"])


@enrutador.get("/proyectos/{proyecto_id}/etiquetas",
    summary="Listar etiquetas del proyecto",
    description="Devuelve todas las etiquetas disponibles en el proyecto.")
async def listar_etiquetas(proyecto_id: str, _: dict = Depends(obtener_usuario_actual)):
    return await servicio_tarea.listar_etiquetas(proyecto_id)