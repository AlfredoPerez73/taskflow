"""
PATRÓN SINGLETON — ConexionMongoDB
Garantiza que exista una única instancia del cliente de base de datos
durante todo el ciclo de vida de la aplicación. Evita abrir múltiples
conexiones TCP innecesarias al mismo cluster de MongoDB Atlas.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.configuracion import configuracion


class ConexionMongoDB:
    _instancia: "ConexionMongoDB | None" = None
    _cliente: AsyncIOMotorClient | None = None

    def __new__(cls) -> "ConexionMongoDB":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    @classmethod
    def obtener_instancia(cls) -> "ConexionMongoDB":
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    def conectar(self) -> None:
        if self._cliente is None:
            self._cliente = AsyncIOMotorClient(configuracion.mongodb_url)

    def desconectar(self) -> None:
        if self._cliente:
            self._cliente.close()
            self._cliente = None

    def obtener_base_datos(self) -> AsyncIOMotorDatabase:
        if self._cliente is None:
            raise RuntimeError("La conexión a MongoDB no ha sido inicializada")
        return self._cliente[configuracion.nombre_bd]