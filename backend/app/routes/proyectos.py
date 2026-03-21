from fastapi import APIRouter, Depends
from app.schemas.proyectos import CrearProyecto, ActualizarProyecto, InvitarMiembro
from app.services import servicio_proyecto
from app.core.dependencias import obtener_usuario_actual, requerir_rol

enrutador = APIRouter(prefix="/proyectos", tags=["Proyectos"])


@enrutador.get("/")
async def listar(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_proyecto.listar_proyectos(usuario["_id"], usuario["rol"])


@enrutador.get("/{proyecto_id}")
async def obtener(proyecto_id: str, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_proyecto.obtener_proyecto(proyecto_id, usuario["_id"], usuario["rol"])


@enrutador.get("/{proyecto_id}/miembros")
async def miembros(proyecto_id: str, _: dict = Depends(obtener_usuario_actual)):
    return await servicio_proyecto.obtener_miembros_proyecto(proyecto_id)


@enrutador.post("/", status_code=201)
async def crear(
    datos: CrearProyecto,
    usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN")),
):
    return await servicio_proyecto.crear_proyecto(datos, usuario["_id"])


@enrutador.put("/{proyecto_id}")
async def actualizar(
    proyecto_id: str,
    datos: ActualizarProyecto,
    usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN")),
):
    return await servicio_proyecto.actualizar_proyecto(proyecto_id, datos, usuario["_id"], usuario["rol"])


@enrutador.delete("/{proyecto_id}")
async def eliminar(
    proyecto_id: str,
    usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN")),
):
    return await servicio_proyecto.eliminar_proyecto(proyecto_id, usuario["_id"], usuario["rol"])


@enrutador.post("/{proyecto_id}/archivar")
async def archivar(
    proyecto_id: str,
    usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN")),
):
    return await servicio_proyecto.archivar_proyecto(proyecto_id, usuario["_id"], usuario["rol"])


@enrutador.post("/{proyecto_id}/invitar")
async def invitar(
    proyecto_id: str,
    datos: InvitarMiembro,
    usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN")),
):
    return await servicio_proyecto.invitar_miembro(proyecto_id, datos, usuario["_id"], usuario["rol"])


@enrutador.post("/{proyecto_id}/clonar", status_code=201)
async def clonar(
    proyecto_id: str,
    usuario: dict = Depends(requerir_rol("PROJECT_MANAGER", "ADMIN")),
):
    return await servicio_proyecto.clonar_proyecto_servicio(proyecto_id, usuario["_id"], usuario["rol"])