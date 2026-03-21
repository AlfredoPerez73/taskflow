"""
PATRÓN PROTOTYPE — Clonadores
Permite crear nuevos objetos copiando (clonando) un objeto existente
como prototipo. En TaskFlow se usa para clonar tareas y proyectos
sin repetir toda la lógica de construcción desde cero, generando
nuevos IDs y limpiando el estado propio del original.
"""
import copy
import uuid
from datetime import datetime, timezone
from typing import Optional


def clonar_tarea(tarea_original: dict, columna_id_destino: Optional[str] = None) -> dict:
    """Clona una tarea existente generando un nuevo ID y reseteando su estado."""
    clon = copy.deepcopy(tarea_original)
    ahora = datetime.now(timezone.utc)

    clon["_id"] = str(uuid.uuid4())
    clon["titulo"] = f"[Copia] {tarea_original.get('titulo', '')}"
    clon["columnaId"] = columna_id_destino or tarea_original["columnaId"]
    clon["horasRegistradas"] = 0.0
    clon["estaVencida"] = False
    clon["subtareas"] = []
    clon["creadoEn"] = ahora
    clon["actualizadoEn"] = ahora

    return clon


def clonar_proyecto(
    proyecto_original: dict,
    tableros_originales: list[dict],
    columnas_originales: list[dict],
    nuevo_propietario_id: str,
) -> dict:
    """
    Clona la estructura de un proyecto (tableros y columnas) sin copiar tareas.
    Retorna un dict con el nuevo proyecto y su estructura.
    """
    ahora = datetime.now(timezone.utc)

    nuevo_proyecto = copy.deepcopy(proyecto_original)
    nuevo_proyecto["_id"] = str(uuid.uuid4())
    nuevo_proyecto["nombre"] = f"[Copia] {proyecto_original.get('nombre', '')}"
    nuevo_proyecto["propietarioId"] = nuevo_propietario_id
    nuevo_proyecto["estado"] = "PLANIFICADO"
    nuevo_proyecto["estaArchivado"] = False
    nuevo_proyecto["miembros"] = [nuevo_propietario_id]
    nuevo_proyecto["creadoEn"] = ahora
    nuevo_proyecto["actualizadoEn"] = ahora

    mapa_id_tablero: dict[str, str] = {}
    nuevos_tableros = []
    for tablero in tableros_originales:
        nuevo_id = str(uuid.uuid4())
        mapa_id_tablero[tablero["_id"]] = nuevo_id
        nuevo_tablero = copy.deepcopy(tablero)
        nuevo_tablero["_id"] = nuevo_id
        nuevo_tablero["proyectoId"] = nuevo_proyecto["_id"]
        nuevo_tablero["creadoEn"] = ahora
        nuevos_tableros.append(nuevo_tablero)

    nuevas_columnas = []
    for columna in columnas_originales:
        nuevo_tablero_id = mapa_id_tablero.get(columna["tableroId"])
        if not nuevo_tablero_id:
            continue
        nueva_columna = copy.deepcopy(columna)
        nueva_columna["_id"] = str(uuid.uuid4())
        nueva_columna["tableroId"] = nuevo_tablero_id
        nuevas_columnas.append(nueva_columna)

    return {
        "proyecto": nuevo_proyecto,
        "tableros": nuevos_tableros,
        "columnas": nuevas_columnas,
    }