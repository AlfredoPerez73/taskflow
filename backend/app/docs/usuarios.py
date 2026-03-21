from fastapi import APIRouter, Depends
from typing import List
from app.schemas.usuarios import RegistroUsuario, LoginUsuario, ActualizarPerfil, RespuestaUsuario, RespuestaToken
from app.services import servicio_usuario
from app.core.dependencias import obtener_usuario_actual, requerir_rol

enrutador = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@enrutador.post("/registro", status_code=201, response_model=RespuestaUsuario,
    summary="Registrar nuevo usuario",
    description="Crea una nueva cuenta. No requiere autenticación. El rol por defecto es DEVELOPER.")
async def registrar(datos: RegistroUsuario):
    return await servicio_usuario.registrar_usuario(datos)


@enrutador.post("/login", response_model=RespuestaToken,
    summary="Iniciar sesión",
    description="Autentica con email y contraseña. Devuelve un **token JWT** válido por 8 horas. Registra el último acceso del usuario.")
async def login(datos: LoginUsuario):
    return await servicio_usuario.iniciar_sesion(datos)


@enrutador.get("/perfil", response_model=RespuestaUsuario,
    summary="Obtener perfil propio",
    description="Devuelve los datos del usuario autenticado actualmente.")
async def obtener_perfil(usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_usuario.obtener_perfil(usuario["_id"])


@enrutador.put("/perfil", response_model=RespuestaUsuario,
    summary="Actualizar perfil propio",
    description="Actualiza nombre, URL de avatar y descripción del usuario autenticado.")
async def actualizar_perfil(datos: ActualizarPerfil, usuario: dict = Depends(obtener_usuario_actual)):
    return await servicio_usuario.actualizar_perfil(usuario["_id"], datos)


@enrutador.get("/", response_model=List[RespuestaUsuario],
    summary="Listar todos los usuarios",
    description="Devuelve todos los usuarios del sistema. **Solo ADMIN.**")
async def listar_usuarios(usuario: dict = Depends(requerir_rol("ADMIN"))):
    return await servicio_usuario.listar_usuarios(usuario)


@enrutador.get("/activos", response_model=List[RespuestaUsuario],
    summary="Listar usuarios activos",
    description="Devuelve todos los usuarios con cuenta activa. Usado internamente para asignar responsables a tareas.")
async def listar_activos(_: dict = Depends(obtener_usuario_actual)):
    return await servicio_usuario.listar_usuarios_activos()


@enrutador.put("/{usuario_id}/desactivar", response_model=RespuestaUsuario,
    summary="Desactivar cuenta de usuario",
    description="Desactiva la cuenta. El usuario no podrá iniciar sesión. **Solo ADMIN.**")
async def desactivar(usuario_id: str, _: dict = Depends(requerir_rol("ADMIN"))):
    return await servicio_usuario.desactivar_usuario(usuario_id)


@enrutador.put("/{usuario_id}/rol", response_model=RespuestaUsuario,
    summary="Cambiar rol de usuario",
    description="Asigna un nuevo rol (ADMIN, PROJECT_MANAGER, DEVELOPER). **Solo ADMIN.**")
async def cambiar_rol(usuario_id: str, cuerpo: dict, _: dict = Depends(requerir_rol("ADMIN"))):
    return await servicio_usuario.cambiar_rol(usuario_id, cuerpo.get("rol", ""))