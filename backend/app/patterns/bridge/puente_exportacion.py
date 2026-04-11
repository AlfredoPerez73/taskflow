"""
PATRÓN BRIDGE — Exportación de reportes
Separa la abstracción del reporte (qué exportar) de su implementación (cómo exportarlo).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from io import BytesIO, StringIO
import csv
import json
from typing import Any

from app.db.conexion import ConexionMongoDB
from app.services import servicio_reporte


class ExportadorImplementacion(ABC):
    @abstractmethod
    def exportar(self, reporte: dict[str, Any]) -> bytes:
        pass

    @abstractmethod
    def extension(self) -> str:
        pass

    @abstractmethod
    def mime_type(self) -> str:
        pass


class ReporteExportable(ABC):
    def __init__(self, exportador: ExportadorImplementacion):
        self.exportador = exportador

    def establecer_exportador(self, exportador: ExportadorImplementacion) -> None:
        self.exportador = exportador

    @abstractmethod
    async def construir_datos(self, proyecto_id: str, usuario: dict) -> dict[str, Any]:
        pass

    async def exportar(self, proyecto_id: str, usuario: dict) -> tuple[bytes, str, str]:
        datos = await self.construir_datos(proyecto_id, usuario)
        contenido = self.exportador.exportar(datos)
        return contenido, self.exportador.mime_type(), self._nombre_archivo(datos)

    def _nombre_archivo(self, datos: dict[str, Any]) -> str:
        marca = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        sufijo = datos.get("tipoReporte", "reporte")
        return f"{sufijo}_{marca}{self.exportador.extension()}"


class ReporteTareas(ReporteExportable):
    async def construir_datos(self, proyecto_id: str, usuario: dict) -> dict[str, Any]:
        db = ConexionMongoDB.obtener_instancia().obtener_base_datos()
        proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
        if not proyecto:
            raise ValueError("Proyecto no encontrado")
        if usuario.get("rol") != "ADMIN" and usuario["_id"] not in proyecto.get("miembros", []):
            raise PermissionError("Sin acceso al proyecto")

        metricas = await servicio_reporte.obtener_metricas_proyecto(proyecto_id)
        tareas = [t async for t in db["tareas"].find({"proyectoId": proyecto_id})]

        filas: list[dict[str, Any]] = []
        for tarea in tareas:
            filas.append(
                {
                    "id": tarea.get("_id"),
                    "titulo": tarea.get("titulo", ""),
                    "tipo": tarea.get("tipo", ""),
                    "prioridad": tarea.get("prioridad", ""),
                    "columnaId": tarea.get("columnaId", ""),
                    "responsables": ", ".join(tarea.get("responsables", [])),
                    "vencimiento": _formatear_fecha(tarea.get("fechaVencimiento")),
                }
            )

        return {
            "tipoReporte": "reporte_tareas",
            "titulo": f"Reporte de tareas - {proyecto.get('nombre', proyecto_id)}",
            "proyectoId": proyecto_id,
            "proyectoNombre": proyecto.get("nombre", proyecto_id),
            "generadoEn": datetime.now(timezone.utc).isoformat(),
            "resumen": {
                "totalTareas": metricas.get("totalTareas", 0),
                "tareasVencidas": metricas.get("tareasVencidas", 0),
                "tareasCompletadas": metricas.get("tareasCompletadas", 0),
                "progreso": metricas.get("progreso", 0),
            },
            "filas": filas,
        }


class ReporteAuditoria(ReporteExportable):
    async def construir_datos(self, proyecto_id: str, usuario: dict) -> dict[str, Any]:
        db = ConexionMongoDB.obtener_instancia().obtener_base_datos()
        proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
        if not proyecto:
            raise ValueError("Proyecto no encontrado")
        if usuario.get("rol") != "ADMIN" and usuario["_id"] not in proyecto.get("miembros", []):
            raise PermissionError("Sin acceso al proyecto")

        auditoria = await servicio_reporte.obtener_auditoria_proyecto(proyecto_id, pagina=1, limite=200)
        filas = []
        for r in auditoria.get("datos", []):
            filas.append(
                {
                    "accion": r.get("accion", ""),
                    "tipoEntidad": r.get("tipoEntidad", ""),
                    "entidadId": r.get("entidadId", ""),
                    "usuarioId": r.get("usuarioId", ""),
                    "marca": _formatear_fecha(r.get("marca")),
                }
            )

        return {
            "tipoReporte": "reporte_auditoria",
            "titulo": f"Reporte de auditoria - {proyecto.get('nombre', proyecto_id)}",
            "proyectoId": proyecto_id,
            "proyectoNombre": proyecto.get("nombre", proyecto_id),
            "generadoEn": datetime.now(timezone.utc).isoformat(),
            "resumen": {
                "totalRegistros": auditoria.get("total", len(filas)),
                "pagina": auditoria.get("pagina", 1),
                "limite": auditoria.get("limite", 200),
            },
            "filas": filas,
        }


class ReporteEquipo(ReporteExportable):
    async def construir_datos(self, proyecto_id: str, usuario: dict) -> dict[str, Any]:
        db = ConexionMongoDB.obtener_instancia().obtener_base_datos()
        proyecto = await db["proyectos"].find_one({"_id": proyecto_id})
        if not proyecto:
            raise ValueError("Proyecto no encontrado")
        if usuario.get("rol") != "ADMIN" and usuario["_id"] not in proyecto.get("miembros", []):
            raise PermissionError("Sin acceso al proyecto")

        metricas = await servicio_reporte.obtener_metricas_proyecto(proyecto_id)
        miembros = [u async for u in db["usuarios"].find({"_id": {"$in": proyecto.get("miembros", [])}})]
        por_usuario = metricas.get("tareasPorUsuario", {})
        filas = []
        for miembro in miembros:
            filas.append(
                {
                    "usuarioId": miembro.get("_id", ""),
                    "nombre": miembro.get("nombre", ""),
                    "email": miembro.get("email", ""),
                    "rol": miembro.get("rol", ""),
                    "tareasAsignadas": por_usuario.get(miembro.get("_id", ""), 0),
                }
            )

        return {
            "tipoReporte": "reporte_equipo",
            "titulo": f"Reporte de equipo - {proyecto.get('nombre', proyecto_id)}",
            "proyectoId": proyecto_id,
            "proyectoNombre": proyecto.get("nombre", proyecto_id),
            "generadoEn": datetime.now(timezone.utc).isoformat(),
            "resumen": {
                "totalMiembros": len(filas),
                "totalTareas": metricas.get("totalTareas", 0),
                "progreso": metricas.get("progreso", 0),
            },
            "filas": filas,
        }


class ExportadorJSON(ExportadorImplementacion):
    def exportar(self, reporte: dict[str, Any]) -> bytes:
        return json.dumps(reporte, ensure_ascii=False, indent=2, default=str).encode("utf-8")

    def extension(self) -> str:
        return ".json"

    def mime_type(self) -> str:
        return "application/json"


class ExportadorCSV(ExportadorImplementacion):
    def exportar(self, reporte: dict[str, Any]) -> bytes:
        out = StringIO()
        writer = csv.writer(out)
        writer.writerow(["titulo", reporte.get("titulo", "")])
        writer.writerow(["proyecto", reporte.get("proyectoNombre", "")])
        writer.writerow(["generadoEn", reporte.get("generadoEn", "")])
        writer.writerow([])
        for k, v in (reporte.get("resumen") or {}).items():
            writer.writerow([k, v])
        writer.writerow([])

        filas = reporte.get("filas", [])
        if filas:
            headers = list(filas[0].keys())
            writer.writerow(headers)
            for fila in filas:
                writer.writerow([fila.get(h, "") for h in headers])
        else:
            writer.writerow(["sin_datos"])

        return out.getvalue().encode("utf-8")

    def extension(self) -> str:
        return ".csv"

    def mime_type(self) -> str:
        return "text/csv; charset=utf-8"


class ExportadorPDF(ExportadorImplementacion):
    def exportar(self, reporte: dict[str, Any]) -> bytes:
        lineas: list[str] = []
        lineas.append(reporte.get("titulo", "Reporte"))
        lineas.append(f"Proyecto: {reporte.get('proyectoNombre', '')}")
        lineas.append(f"Generado: {reporte.get('generadoEn', '')}")
        lineas.append("")
        lineas.append("Resumen:")
        for k, v in (reporte.get("resumen") or {}).items():
            lineas.append(f"- {k}: {v}")
        lineas.append("")
        lineas.append("Detalle:")
        for idx, fila in enumerate(reporte.get("filas", []), start=1):
            pares = " | ".join(f"{k}={fila.get(k, '')}" for k in fila.keys())
            lineas.append(f"{idx}. {pares}")

        contenido_texto = "\n".join(lineas)
        return _crear_pdf_simple(contenido_texto)

    def extension(self) -> str:
        return ".pdf"

    def mime_type(self) -> str:
        return "application/pdf"


def _formatear_fecha(valor: Any) -> str:
    if not valor:
        return ""
    if isinstance(valor, datetime):
        return valor.astimezone(timezone.utc).isoformat()
    return str(valor)


def _crear_pdf_simple(texto: str) -> bytes:
    """
    Genera un PDF básico sin dependencias externas.
    """
    def _escape_pdf(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    lineas = texto.splitlines() or [""]
    comandos: list[str] = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
    for i, linea in enumerate(lineas):
        if i > 0:
            comandos.append("T*")
        comandos.append(f"({_escape_pdf(linea)}) Tj")
    comandos.append("ET")
    stream = "\n".join(comandos).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
    )
    objects.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    objects.append(
        f"5 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("ascii")
        + stream
        + b"\nendstream\nendobj\n"
    )

    output = BytesIO()
    output.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj in objects:
        offsets.append(output.tell())
        output.write(obj)

    xref_start = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        output.write(f"{off:010d} 00000 n \n".encode("ascii"))
    output.write(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_start}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return output.getvalue()

