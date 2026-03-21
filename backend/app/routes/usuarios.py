from fastapi import APIRouter, Depends
from app.schemas.usuarios import RegistroUsuario, LoginUsuario, ActualizarPerfil
from app.services import servicio_usuario
from app.core.dependencias import obtener_usuario_actual, requerir_rol

enrutador = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Cualquier visitante puede registrarse e iniciar sesión (RF-01: Usuario)
@enrutador.post("/registro", status_code=201)
async def registrar(datos: RegistroUsuario):
    return await servicio_usuario.registrar_usuario(datos)


@enrutador.post("/login")
async def login(datos: LoginUsuario):
    return await servicio_usuario.iniciar_sesion(datos)


# Cualquier usuario autenticado puede ver y actualizar su propio perfil (RF-01: Usuario)
@enrutador.get("/perfil")
async def obtener_perfil(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_usuario.obtener_perfil(usuario["_id"])


@enrutador.put("/perfil")
async def actualizar_perfil(
    datos: ActualizarPerfil,
    usuario: dict = Depends(obtener_usuario_actual),
):
    return await servicio_usuario.actualizar_perfil(usuario["_id"], datos)


# Solo ADMIN puede gestionar cuentas y asignar roles (RF-01: Admin)
@enrutador.get("/")
async def listar_usuarios(usuario: dict = Depends(requerir_rol("ADMIN"))):
    return await servicio_usuario.listar_usuarios(usuario)


@enrutador.put("/{usuario_id}/desactivar")
async def desactivar(
    usuario_id: str,
    _: dict = Depends(requerir_rol("ADMIN")),
):
    return await servicio_usuario.desactivar_usuario(usuario_id)


@enrutador.put("/{usuario_id}/rol")
async def cambiar_rol(
    usuario_id: str,
    cuerpo: dict,
    _: dict = Depends(requerir_rol("ADMIN")),
):
    return await servicio_usuario.cambiar_rol(usuario_id, cuerpo.get("rol", ""))


@enrutador.get("/activos")
async def listar_activos(_: dict = Depends(obtener_usuario_actual)):
    """Devuelve todos los usuarios activos para poder asignarlos como responsables."""
    return await servicio_usuario.listar_usuarios_activos()