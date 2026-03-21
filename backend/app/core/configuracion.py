from pydantic_settings import BaseSettings


class Configuracion(BaseSettings):
    mongodb_url: str
    nombre_bd: str = "taskflow"
    clave_secreta_jwt: str
    algoritmo_jwt: str = "HS256"
    minutos_expiracion_token: int = 480
    puerto: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


configuracion = Configuracion()