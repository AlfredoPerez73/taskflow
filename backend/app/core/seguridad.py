from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, status
from app.core.configuracion import configuracion


def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    return bcrypt.checkpw(
        contrasena_plana.encode("utf-8"),
        contrasena_hash.encode("utf-8"),
    )


def generar_hash_contrasena(contrasena: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(contrasena.encode("utf-8"), salt).decode("utf-8")


def crear_token_acceso(datos: dict) -> str:
    datos_copia = datos.copy()
    expiracion = datetime.now(timezone.utc) + timedelta(
        minutes=configuracion.minutos_expiracion_token
    )
    datos_copia.update({"exp": expiracion})
    return jwt.encode(
        datos_copia,
        configuracion.clave_secreta_jwt,
        algorithm=configuracion.algoritmo_jwt,
    )


def verificar_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            configuracion.clave_secreta_jwt,
            algorithms=[configuracion.algoritmo_jwt],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )