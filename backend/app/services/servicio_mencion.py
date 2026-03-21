"""
Servicio de menciones @usuario en comentarios.
Detecta patrones @nombre o @id en el texto y genera notificaciones.
"""
import re
from app.services.servicio_notificacion import crear_notificacion_interna


_PATRON_MENCION = re.compile(r"@([\w\.\-]+)")


async def extraer_y_notificar_menciones(
    db,
    texto: str,
    autor_id: str,
    tarea_titulo: str,
    proyecto_id: str,
    tarea_id: str | None = None,
) -> list[str]:
    """
    Extrae menciones del texto, resuelve los usuarios por nombre o email,
    crea notificaciones y devuelve los IDs de usuarios mencionados.
    """
    tokens = _PATRON_MENCION.findall(texto)
    if not tokens:
        return []

    mencionados: list[str] = []
    for token in set(tokens):
        # Buscar usuario por nombre (case-insensitive) o por email
        usuario = await db["usuarios"].find_one({
            "$or": [
                {"nombre": {"$regex": f"^{re.escape(token)}$", "$options": "i"}},
                {"email": {"$regex": f"^{re.escape(token)}$", "$options": "i"}},
            ],
            "estaActivo": True,
        })
        if usuario and usuario["_id"] != autor_id:
            mencionados.append(usuario["_id"])
            await crear_notificacion_interna(
                db,
                usuario["_id"],
                f"Te mencionaron en la tarea \"{tarea_titulo}\"",
                "MENCION_EN_COMENTARIO",
                tarea_id=tarea_id,
                proyecto_id=proyecto_id,
                titulo_tarea=tarea_titulo,
            )

    return mencionados


def resaltar_menciones(texto: str) -> str:
    """
    Convierte @usuario en marcado HTML para mostrar en el frontend.
    El frontend usa esto para renderizar chips de mención.
    """
    return _PATRON_MENCION.sub(
        lambda m: f'<span class="mencion">@{m.group(1)}</span>', texto
    )