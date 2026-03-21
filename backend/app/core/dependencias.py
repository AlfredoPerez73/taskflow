from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.seguridad import verificar_token
from app.db.conexion import ConexionMongoDB

esquema_bearer = HTTPBearer()


async def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer),
) -> dict:
    payload = verificar_token(credenciales.credentials)
    usuario_id = payload.get("sub")
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin identificador de usuario",
        )
    db = ConexionMongoDB.obtener_instancia().obtener_base_datos()
    usuario = await db["usuarios"].find_one({"_id": usuario_id})
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    if not usuario.get("estaActivo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )
    return usuario


def requerir_rol(*roles: str):
    async def verificador(usuario: dict = Depends(obtener_usuario_actual)):
        rol_usuario = usuario.get("rol", "")
        if rol_usuario not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los roles: {', '.join(roles)}",
            )
        return usuario
    return verificador