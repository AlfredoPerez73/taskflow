"""
PATRÓN ABSTRACT FACTORY — FabricaTemas
Proporciona una interfaz para crear familias de objetos relacionados
(colores, tipografía, componentes UI) sin especificar sus clases concretas.
Permite cambiar el tema completo de la aplicación intercambiando la fábrica,
sin modificar el código que consume los componentes visuales.
"""
from abc import ABC, abstractmethod
from typing import TypedDict


class ColoresTema(TypedDict):
    fondo: str
    superficie: str
    superficie2: str
    borde: str
    acento: str
    texto: str
    silenciado: str
    verde: str
    ambar: str
    rojo: str
    azul: str


class VariablesTema(TypedDict):
    nombre: str
    colores: ColoresTema
    fuente_base: str
    radio_borde: str


class FabricaTema(ABC):
    """Interfaz abstracta de la Abstract Factory."""

    @abstractmethod
    def crear_colores(self) -> ColoresTema:
        pass

    @abstractmethod
    def crear_variables(self) -> VariablesTema:
        pass


class FabricaTemaOscuro(FabricaTema):
    def crear_colores(self) -> ColoresTema:
        return {
            "fondo": "#0d0d0f",
            "superficie": "#141417",
            "superficie2": "#1c1c22",
            "borde": "#2a2a33",
            "acento": "#e8e0c8",
            "texto": "#e2e2e8",
            "silenciado": "#6b6b8a",
            "verde": "#3ecf8e",
            "ambar": "#f59e0b",
            "rojo": "#ef4444",
            "azul": "#60a5fa",
        }

    def crear_variables(self) -> VariablesTema:
        return {
            "nombre": "oscuro",
            "colores": self.crear_colores(),
            "fuente_base": "Syne, sans-serif",
            "radio_borde": "6px",
        }


class FabricaTemaClaro(FabricaTema):
    def crear_colores(self) -> ColoresTema:
        return {
            "fondo": "#f5f5f0",
            "superficie": "#ffffff",
            "superficie2": "#f0f0eb",
            "borde": "#e0e0d8",
            "acento": "#1a1a2e",
            "texto": "#2a2a35",
            "silenciado": "#8a8a9a",
            "verde": "#16a34a",
            "ambar": "#d97706",
            "rojo": "#dc2626",
            "azul": "#2563eb",
        }

    def crear_variables(self) -> VariablesTema:
        return {
            "nombre": "claro",
            "colores": self.crear_colores(),
            "fuente_base": "Syne, sans-serif",
            "radio_borde": "6px",
        }


class FabricaTemaAzul(FabricaTema):
    def crear_colores(self) -> ColoresTema:
        return {
            "fondo": "#0a1628",
            "superficie": "#0f2040",
            "superficie2": "#162850",
            "borde": "#1e3a6e",
            "acento": "#93c5fd",
            "texto": "#dbeafe",
            "silenciado": "#6b8ab0",
            "verde": "#34d399",
            "ambar": "#fbbf24",
            "rojo": "#f87171",
            "azul": "#60a5fa",
        }

    def crear_variables(self) -> VariablesTema:
        return {
            "nombre": "azul",
            "colores": self.crear_colores(),
            "fuente_base": "Syne, sans-serif",
            "radio_borde": "6px",
        }


_fabricas: dict[str, FabricaTema] = {
    "oscuro": FabricaTemaOscuro(),
    "claro": FabricaTemaClaro(),
    "azul": FabricaTemaAzul(),
}


def obtener_fabrica_tema(nombre_tema: str) -> FabricaTema:
    fabrica = _fabricas.get(nombre_tema)
    if not fabrica:
        raise ValueError(f"Tema no soportado: {nombre_tema}")
    return fabrica


def obtener_variables_tema(nombre_tema: str) -> VariablesTema:
    return obtener_fabrica_tema(nombre_tema).crear_variables()