from enum import Enum


class Rol(str, Enum):
    ADMIN = "ADMIN"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    DEVELOPER = "DEVELOPER"


class EstadoProyecto(str, Enum):
    PLANIFICADO = "PLANIFICADO"
    EN_PROGRESO = "EN_PROGRESO"
    PAUSADO = "PAUSADO"
    COMPLETADO = "COMPLETADO"
    ARCHIVADO = "ARCHIVADO"


class PrioridadTarea(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"


class TipoTarea(str, Enum):
    BUG = "BUG"
    FEATURE = "FEATURE"
    TASK = "TASK"
    IMPROVEMENT = "IMPROVEMENT"


class TipoNotificacion(str, Enum):
    TAREA_ASIGNADA = "TAREA_ASIGNADA"
    TAREA_VENCIDA = "TAREA_VENCIDA"
    COMENTARIO_EN_TAREA = "COMENTARIO_EN_TAREA"
    ESTADO_TAREA_CAMBIADO = "ESTADO_TAREA_CAMBIADO"
    MIEMBRO_INVITADO = "MIEMBRO_INVITADO"


class CanalNotificacion(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    AMBOS = "AMBOS"


class TipoMencion(str, Enum):
    COMENTARIO = "COMENTARIO"