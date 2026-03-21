from datetime import datetime, timezone
from fastapi import HTTPException, status
import uuid

from app.db.conexion import ConexionMongoDB
from app.core.seguridad import generar_hash_contrasena, verificar_contrasena, crear_token_acceso
from app.schemas.usuarios import RegistroUsuario, LoginUsuario, ActualizarPerfil


def _db():
    return ConexionMongoDB.obtener_instancia().obtener_base_datos()


def _serializar_usuario(doc: dict) -> dict:
    return {
        "id": doc["_id"],
        "nombre": doc["nombre"],
        "email": doc["email"],
        "rol": doc["rol"],
        "avatarUri": doc.get("avatarUri"),
        "descripcion": doc.get("descripcion"),
        "ultimoAcceso": doc.get("ultimoAcceso"),
        "estaActivo": doc.get("estaActivo", True),
    }


async def registrar_usuario(datos: RegistroUsuario) -> dict:
    db = _db()
    existente = await db["usuarios"].find_one({"email": datos.email})
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese correo electrónico",
        )
    nuevo = {
        "_id": str(uuid.uuid4()),
        "nombre": datos.nombre,
        "email": datos.email,
        "passwordHash": generar_hash_contrasena(datos.contrasena),
        "rol": datos.rol.value,
        "avatarUri": None,
        "descripcion": None,
        "ultimoAcceso": None,
        "estaActivo": True,
        "creadoEn": datetime.now(timezone.utc),
    }
    await db["usuarios"].insert_one(nuevo)
    return _serializar_usuario(nuevo)


async def iniciar_sesion(datos: LoginUsuario) -> dict:
    db = _db()
    usuario = await db["usuarios"].find_one({"email": datos.email})
    if not usuario or not verificar_contrasena(datos.contrasena, usuario["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    if not usuario.get("estaActivo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )
    await db["usuarios"].update_one(
        {"_id": usuario["_id"]},
        {"$set": {"ultimoAcceso": datetime.now(timezone.utc)}},
    )
    usuario["ultimoAcceso"] = datetime.now(timezone.utc)
    token = crear_token_acceso({"sub": usuario["_id"], "rol": usuario["rol"]})
    return {
        "token_acceso": token,
        "tipo_token": "bearer",
        "usuario": _serializar_usuario(usuario),
    }


async def obtener_perfil(usuario_id: str) -> dict:
    db = _db()
    usuario = await db["usuarios"].find_one({"_id": usuario_id})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _serializar_usuario(usuario)


async def actualizar_perfil(usuario_id: str, datos: ActualizarPerfil) -> dict:
    db = _db()
    cambios = {k: v for k, v in datos.model_dump().items() if v is not None}
    cambios["actualizadoEn"] = datetime.now(timezone.utc)
    await db["usuarios"].update_one({"_id": usuario_id}, {"$set": cambios})
    return await obtener_perfil(usuario_id)


async def listar_usuarios(usuario_actual: dict) -> list:
    db = _db()
    cursor = db["usuarios"].find({}, {"passwordHash": 0})
    return [_serializar_usuario(u) async for u in cursor]


async def desactivar_usuario(usuario_id: str) -> dict:
    db = _db()
    await db["usuarios"].update_one(
        {"_id": usuario_id},
        {"$set": {"estaActivo": False, "actualizadoEn": datetime.now(timezone.utc)}},
    )
    return await obtener_perfil(usuario_id)


async def cambiar_rol(usuario_id: str, nuevo_rol: str) -> dict:
    db = _db()
    roles_validos = {"ADMIN", "PROJECT_MANAGER", "DEVELOPER"}
    if nuevo_rol not in roles_validos:
        raise HTTPException(status_code=400, detail="Rol no válido")
    await db["usuarios"].update_one(
        {"_id": usuario_id},
        {"$set": {"rol": nuevo_rol, "actualizadoEn": datetime.now(timezone.utc)}},
    )
    return await obtener_perfil(usuario_id)


async def listar_usuarios_activos() -> list:
    db = _db()
    cursor = db["usuarios"].find({"estaActivo": True}, {"passwordHash": 0})
    return [_serializar_usuario(u) async for u in cursor]