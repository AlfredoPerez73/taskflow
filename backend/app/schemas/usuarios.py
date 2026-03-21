from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.enums import Rol


class RegistroUsuario(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=80)
    email: EmailStr
    contrasena: str = Field(..., min_length=6)
    rol: Rol = Rol.DEVELOPER


class LoginUsuario(BaseModel):
    email: EmailStr
    contrasena: str


class ActualizarPerfil(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=80)
    avatarUri: Optional[str] = None
    descripcion: Optional[str] = None


class RespuestaUsuario(BaseModel):
    id: str
    nombre: str
    email: str
    rol: str
    avatarUri: Optional[str] = None
    descripcion: Optional[str] = None
    ultimoAcceso: Optional[datetime] = None
    estaActivo: bool


class RespuestaToken(BaseModel):
    token_acceso: str
    tipo_token: str = "bearer"
    usuario: RespuestaUsuario