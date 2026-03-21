from pydantic import BaseModel, Field
from typing import TypeVar, Generic, List, Optional

T = TypeVar("T")


class ParametrosPaginacion(BaseModel):
    pagina: int = Field(1, ge=1, description="Número de página (empieza en 1)")
    limite: int = Field(20, ge=1, le=100, description="Ítems por página (máx 100)")


class RespuestaPaginada(BaseModel):
    datos: List[dict]
    pagina: int
    limite: int
    total: int
    totalPaginas: int
    tieneSiguiente: bool
    tieneAnterior: bool