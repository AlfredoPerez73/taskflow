"""
PATRÓN FACTORY METHOD — FabricaTareas
Define una interfaz (CreadorTarea) para crear objetos, pero delega
a las subclases (CreadorBug, CreadorFeature, etc.) la decisión de
qué clase concreta instanciar. Permite agregar nuevos tipos de tarea
sin modificar el código existente.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.enums import TipoTarea, PrioridadTarea


class CreadorTarea(ABC):
    """Interfaz base del Factory Method."""

    @abstractmethod
    def crear(
        self,
        titulo: str,
        columna_id: str,
        proyecto_id: str,
        creado_por: str,
        descripcion: Optional[str] = None,
        responsables: Optional[list] = None,
        fecha_vencimiento: Optional[datetime] = None,
        horas_estimadas: Optional[float] = None,
        etiquetas: Optional[list] = None,
    ) -> dict:
        pass

    def _base(
        self,
        titulo: str,
        tipo: TipoTarea,
        prioridad: PrioridadTarea,
        columna_id: str,
        proyecto_id: str,
        creado_por: str,
        descripcion: Optional[str],
        responsables: Optional[list],
        fecha_vencimiento: Optional[datetime],
        horas_estimadas: Optional[float],
        etiquetas: Optional[list],
    ) -> dict:
        ahora = datetime.now(timezone.utc)
        return {
            "_id": str(uuid.uuid4()),
            "titulo": titulo,
            "descripcion": descripcion,
            "tipo": tipo.value,
            "prioridad": prioridad.value,
            "columnaId": columna_id,
            "proyectoId": proyecto_id,
            "creadoPor": creado_por,
            "responsables": responsables or [],
            "etiquetas": etiquetas or [],
            "subtareas": [],
            "fechaVencimiento": fecha_vencimiento,
            "horasEstimadas": horas_estimadas,
            "horasRegistradas": 0.0,
            "estaVencida": False,
            "creadoEn": ahora,
            "actualizadoEn": ahora,
        }


class CreadorBug(CreadorTarea):
    def crear(self, titulo, columna_id, proyecto_id, creado_por,
              descripcion=None, responsables=None, fecha_vencimiento=None,
              horas_estimadas=None, etiquetas=None) -> dict:
        tarea = self._base(
            titulo, TipoTarea.BUG, PrioridadTarea.ALTA,
            columna_id, proyecto_id, creado_por,
            descripcion, responsables, fecha_vencimiento, horas_estimadas, etiquetas
        )
        tarea["metadatos"] = {"requiereReproduccion": True, "severidad": "alta"}
        return tarea


class CreadorFeature(CreadorTarea):
    def crear(self, titulo, columna_id, proyecto_id, creado_por,
              descripcion=None, responsables=None, fecha_vencimiento=None,
              horas_estimadas=None, etiquetas=None) -> dict:
        tarea = self._base(
            titulo, TipoTarea.FEATURE, PrioridadTarea.MEDIA,
            columna_id, proyecto_id, creado_por,
            descripcion, responsables, fecha_vencimiento, horas_estimadas, etiquetas
        )
        tarea["metadatos"] = {"requiereRevisionDiseno": True}
        return tarea


class CreadorTaskGeneral(CreadorTarea):
    def crear(self, titulo, columna_id, proyecto_id, creado_por,
              descripcion=None, responsables=None, fecha_vencimiento=None,
              horas_estimadas=None, etiquetas=None) -> dict:
        return self._base(
            titulo, TipoTarea.TASK, PrioridadTarea.MEDIA,
            columna_id, proyecto_id, creado_por,
            descripcion, responsables, fecha_vencimiento, horas_estimadas, etiquetas
        )


class CreadorMejora(CreadorTarea):
    def crear(self, titulo, columna_id, proyecto_id, creado_por,
              descripcion=None, responsables=None, fecha_vencimiento=None,
              horas_estimadas=None, etiquetas=None) -> dict:
        tarea = self._base(
            titulo, TipoTarea.IMPROVEMENT, PrioridadTarea.BAJA,
            columna_id, proyecto_id, creado_por,
            descripcion, responsables, fecha_vencimiento, horas_estimadas, etiquetas
        )
        tarea["metadatos"] = {"afectaRendimiento": True}
        return tarea


_creadores: dict[str, CreadorTarea] = {
    TipoTarea.BUG.value: CreadorBug(),
    TipoTarea.FEATURE.value: CreadorFeature(),
    TipoTarea.TASK.value: CreadorTaskGeneral(),
    TipoTarea.IMPROVEMENT.value: CreadorMejora(),
}


def obtener_creador(tipo: str) -> CreadorTarea:
    creador = _creadores.get(tipo)
    if not creador:
        raise ValueError(f"Tipo de tarea no soportado: {tipo}")
    return creador