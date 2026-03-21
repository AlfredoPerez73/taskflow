"""
PATRÓN BUILDER — ConstructorTareaAvanzada
Separa la construcción de una tarea compleja de su representación final.
Permite crear tareas paso a paso configurando cada atributo de forma
independiente y fluida, y al final invocar construir() para obtener
el documento listo para insertar en MongoDB.
Se usa cuando una tarea requiere muchas opciones opcionales (subtareas,
etiquetas, adjuntos, tiempo estimado, responsables múltiples, etc.).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from app.models.enums import PrioridadTarea, TipoTarea


class ConstructorTareaAvanzada:
    def __init__(self) -> None:
        self._reiniciar()

    def _reiniciar(self) -> None:
        self._datos: dict = {
            "_id": str(uuid.uuid4()),
            "titulo": "",
            "descripcion": None,
            "tipo": TipoTarea.TASK.value,
            "prioridad": PrioridadTarea.MEDIA.value,
            "columnaId": "",
            "proyectoId": "",
            "creadoPor": "",
            "responsables": [],
            "etiquetas": [],
            "subtareas": [],
            "fechaVencimiento": None,
            "horasEstimadas": None,
            "horasRegistradas": 0.0,
            "estaVencida": False,
            "metadatos": {},
            "creadoEn": datetime.now(timezone.utc),
            "actualizadoEn": datetime.now(timezone.utc),
        }

    def con_titulo(self, titulo: str) -> "ConstructorTareaAvanzada":
        self._datos["titulo"] = titulo
        return self

    def con_descripcion(self, descripcion: str) -> "ConstructorTareaAvanzada":
        self._datos["descripcion"] = descripcion
        return self

    def con_tipo(self, tipo: TipoTarea) -> "ConstructorTareaAvanzada":
        self._datos["tipo"] = tipo.value
        return self

    def con_prioridad(self, prioridad: PrioridadTarea) -> "ConstructorTareaAvanzada":
        self._datos["prioridad"] = prioridad.value
        return self

    def en_columna(self, columna_id: str) -> "ConstructorTareaAvanzada":
        self._datos["columnaId"] = columna_id
        return self

    def en_proyecto(self, proyecto_id: str) -> "ConstructorTareaAvanzada":
        self._datos["proyectoId"] = proyecto_id
        return self

    def creado_por(self, usuario_id: str) -> "ConstructorTareaAvanzada":
        self._datos["creadoPor"] = usuario_id
        return self

    def con_responsables(self, responsables: list[str]) -> "ConstructorTareaAvanzada":
        self._datos["responsables"] = responsables
        return self

    def con_etiquetas(self, etiquetas: list[str]) -> "ConstructorTareaAvanzada":
        self._datos["etiquetas"] = etiquetas
        return self

    def con_subtareas(self, subtareas: list[str]) -> "ConstructorTareaAvanzada":
        self._datos["subtareas"] = subtareas
        return self

    def con_fecha_vencimiento(self, fecha: datetime) -> "ConstructorTareaAvanzada":
        self._datos["fechaVencimiento"] = fecha
        return self

    def con_horas_estimadas(self, horas: float) -> "ConstructorTareaAvanzada":
        self._datos["horasEstimadas"] = horas
        return self

    def con_metadatos(self, metadatos: dict) -> "ConstructorTareaAvanzada":
        self._datos["metadatos"].update(metadatos)
        return self

    def construir(self) -> dict:
        if not self._datos["titulo"]:
            raise ValueError("El título de la tarea es obligatorio")
        if not self._datos["columnaId"]:
            raise ValueError("La columna de la tarea es obligatoria")
        if not self._datos["proyectoId"]:
            raise ValueError("El proyecto de la tarea es obligatorio")
        resultado = dict(self._datos)
        self._reiniciar()
        return resultado