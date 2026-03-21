from fastapi import APIRouter, Depends
from typing import List
from app.schemas.proyectos import CrearProyecto, ActualizarProyecto, InvitarMiembro, RespuestaProyecto
from app.schemas.usuarios import RespuestaUsuario
from app.services import servicio_proyecto
from app.core.dependencias import obtener_usuario_actual, requerir_rol

enrutador = APIRouter(prefix="/proyectos", tags=["Proyectos"])


@enrutador.get("/", response_model=List[RespuestaProyecto],
    summary="Listar proyectos",
    description="**ADMIN** ve todos los proyectos del sistema. **PM y DEV** ven solo los proyectos donde son miembros.")
async def listar(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_proyecto.listar_proyectos(usuario["_id"], usuario["rol"])


@enrutador.get("/{proyecto_id}", response_model=RespuestaProyecto,
    summary="Obtener proyecto por ID",
    description="Devuelve los datos de un proyecto. DEV solo puede acceder si es miembro.")
async def obtener(proyecto_id: str, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_proyecto.obtener_proyecto(proyecto_id, usuario["_id"], usuario["rol"])


@enrutador.get("/{proyecto_id}/miembros", response_model=List[RespuestaUsuario],
    summary="Listar miembros del proyecto",
    description="Devuelve todos los usuarios que pertenecen al proyecto.")
async def miembros(proyecto_id: str, _: dict = Depends(obtener_usuario_actual)):
    return await servicio_proyecto.obtener_miembros_proyecto(proyecto_id)


@enrutador.post("/", status_code=201, response_model=RespuestaProyecto,
    summary="Crear proyecto",
    description="Crea un nuevo proyecto. Genera automáticamente un tablero Kanban con 4 columnas por defecto. Todos los ADMIN son agregados como miembros automáticamente. **PM y ADMIN.**")
async def crear(datos: CrearProyecto, usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_proyecto.crear_proyecto(datos, usuario["_id"])


@enrutador.put("/{proyecto_id}", response_model=RespuestaProyecto,
    summary="Actualizar proyecto",
    description="Actualiza los datos del proyecto. Solo el propietario o ADMIN puede editar. Los proyectos archivados son de solo lectura. **PM y ADMIN.**")
async def actualizar(proyecto_id: str, datos: ActualizarProyecto, usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_proyecto.actualizar_proyecto(proyecto_id, datos, usuario["_id"], usuario["rol"])


@enrutador.delete("/{proyecto_id",
    summary="Eliminar proyecto",
    description="Elimina permanentemente el proyecto. Solo el propietario o ADMIN. **PM y ADMIN.**")
async def eliminar(proyecto_id: str, usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_proyecto.eliminar_proyecto(proyecto_id, usuario["_id"], usuario["rol"])


@enrutador.post("/{proyecto_id}/archivar", response_model=RespuestaProyecto,
    summary="Archivar proyecto",
    description="Marca el proyecto como ARCHIVADO. Los proyectos archivados son de solo lectura. **PM y ADMIN.**")
async def archivar(proyecto_id: str, usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_proyecto.archivar_proyecto(proyecto_id, usuario["_id"], usuario["rol"])


@enrutador.post("/{proyecto_id}/invitar",
    summary="Invitar miembro al proyecto",
    description="Agrega un usuario al proyecto por su correo electrónico. **PM y ADMIN.**")
async def invitar(proyecto_id: str, datos: InvitarMiembro, usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_proyecto.invitar_miembro(proyecto_id, datos, usuario["_id"], usuario["rol"])


@enrutador.post("/{proyecto_id}/clonar", status_code=201, response_model=RespuestaProyecto,
    summary="Clonar proyecto — Patrón Prototype",
    description="**Patrón Prototype:** Copia la estructura completa del proyecto (tableros y columnas) sin incluir las tareas. Genera nuevos UUIDs para todos los elementos clonados. **PM y ADMIN.**")
async def clonar(proyecto_id: str, usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN"))):
    return await servicio_proyecto.clonar_proyecto_servicio(proyecto_id, usuario["_id"], usuario["rol"])