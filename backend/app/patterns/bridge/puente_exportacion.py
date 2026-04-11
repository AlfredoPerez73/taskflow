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
        return _crear_pdf_reporte_estilizado(reporte)

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


def _crear_pdf_reporte_estilizado(reporte: dict[str, Any]) -> bytes:
    """
    Genera un PDF con encabezado visual y secciones legibles sin librerías externas.
    """
    def _escape_pdf(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _items_detalle() -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for idx, fila in enumerate(reporte.get("filas", []), start=1):
            if idx > 28:
                break
            items.append(
                {
                    "numero": idx,
                    "id": fila.get("id") or "-",
                    "titulo": fila.get("titulo") or "-",
                    "tipo": fila.get("tipo") or "-",
                    "prioridad": fila.get("prioridad") or "-",
                    "columnaId": fila.get("columnaId") or "-",
                    "responsables": fila.get("responsables") or "-",
                    "vencimiento": fila.get("vencimiento") or "-",
                }
            )
        return items

    titulo = str(reporte.get("titulo", "Reporte"))
    proyecto = str(reporte.get("proyectoNombre", ""))
    generado = str(reporte.get("generadoEn", ""))
    resumen = reporte.get("resumen") or {}
    resumen_lineas = [f"- {k}: {v}" for k, v in resumen.items()] or ["- Sin metricas disponibles"]
    detalle_items = _items_detalle()

    comandos: list[str] = []
    # Fondo encabezado
    comandos.extend(
        [
            "q",
            "0.12 0.10 0.30 rg",
            "0 770 595 72 re f",
            "Q",
        ]
    )
    # Línea decorativa
    comandos.extend(
        [
            "q",
            "0.42 0.38 0.96 RG",
            "2 w",
            "40 765 m",
            "555 765 l",
            "S",
            "Q",
        ]
    )

    y = 812
    comandos.append("BT")
    comandos.append("/F2 18 Tf")
    comandos.append("1 1 1 rg")
    comandos.append(f"40 {y} Td")
    comandos.append(f"({_escape_pdf(titulo[:72])}) Tj")
    comandos.append("ET")

    meta = f"Proyecto: {proyecto}   |   Generado: {generado}"
    comandos.append("BT")
    comandos.append("/F1 9 Tf")
    comandos.append("0.88 0.88 1 rg")
    comandos.append("40 792 Td")
    comandos.append(f"({_escape_pdf(meta[:120])}) Tj")
    comandos.append("ET")

    # Resumen
    y = 742
    comandos.append("BT")
    comandos.append("/F2 12 Tf")
    comandos.append("0.16 0.18 0.35 rg")
    comandos.append(f"40 {y} Td")
    comandos.append("(Resumen ejecutivo) Tj")
    comandos.append("ET")
    y -= 18

    for linea in resumen_lineas:
        if y < 80:
            break
        for sub in _envolver_texto(linea, 95):
            if y < 80:
                break
            comandos.append("BT")
            comandos.append("/F1 10 Tf")
            comandos.append("0.12 0.12 0.12 rg")
            comandos.append(f"48 {y} Td")
            comandos.append(f"({_escape_pdf(sub)}) Tj")
            comandos.append("ET")
            y -= 13

    y -= 10
    if y > 90:
        comandos.append("BT")
        comandos.append("/F2 12 Tf")
        comandos.append("0.16 0.18 0.35 rg")
        comandos.append(f"40 {y} Td")
        comandos.append("(Detalle) Tj")
        comandos.append("ET")
        y -= 16

    if not detalle_items:
        comandos.append("BT")
        comandos.append("/F1 9 Tf")
        comandos.append("0.25 0.25 0.25 rg")
        comandos.append(f"48 {y} Td")
        comandos.append("(Sin registros para mostrar.) Tj")
        comandos.append("ET")
    else:
        for item in detalle_items:
            if y < 120:
                break
            # tarjeta del ítem
            alto = 90
            top = y + 8
            bottom = top - alto
            comandos.extend(
                [
                    "q",
                    "0.97 0.97 1 rg",
                    f"40 {bottom} 515 {alto} re f",
                    "0.86 0.86 0.95 RG",
                    "0.7 w",
                    f"40 {bottom} 515 {alto} re S",
                    "Q",
                ]
            )
            # título del bloque
            comandos.append("BT")
            comandos.append("/F2 10 Tf")
            comandos.append("0.16 0.18 0.35 rg")
            comandos.append(f"48 {top - 16} Td")
            comandos.append(f"(Item {item['numero']} - { _escape_pdf(str(item['titulo'])[:58]) }) Tj")
            comandos.append("ET")

            linea1 = f"ID: {item['id']}    Tipo: {item['tipo']}    Prioridad: {item['prioridad']}"
            linea2 = f"Columna: {item['columnaId']}"
            linea3 = f"Responsables: {item['responsables']}"
            linea4 = f"Vencimiento: {item['vencimiento']}"

            yy = top - 32
            for linea in [linea1, linea2, linea3, linea4]:
                for sub in _envolver_texto(str(linea), 96):
                    comandos.append("BT")
                    comandos.append("/F1 8.8 Tf")
                    comandos.append("0.16 0.16 0.16 rg")
                    comandos.append(f"50 {yy} Td")
                    comandos.append(f"({_escape_pdf(sub)}) Tj")
                    comandos.append("ET")
                    yy -= 10

            y = bottom - 10

        if len(reporte.get("filas", [])) > len(detalle_items) and y > 40:
            comandos.append("BT")
            comandos.append("/F1 8 Tf")
            comandos.append("0.45 0.45 0.55 rg")
            comandos.append(f"40 {max(y, 36)} Td")
            comandos.append("(Detalle truncado para mantener una presentacion limpia del reporte.) Tj")
            comandos.append("ET")

    # Pie de página
    comandos.append("BT")
    comandos.append("/F1 8 Tf")
    comandos.append("0.45 0.45 0.55 rg")
    comandos.append("40 24 Td")
    comandos.append("(TaskFlow - Reporte generado automaticamente) Tj")
    comandos.append("ET")

    stream = "\n".join(comandos).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>\nendobj\n"
    )
    objects.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    objects.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n")
    objects.append(
        f"6 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("ascii")
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


def _envolver_texto(texto: str, ancho: int) -> list[str]:
    if len(texto) <= ancho:
        return [texto]
    palabras = texto.split(" ")
    lineas: list[str] = []
    actual = ""
    for palabra in palabras:
        candidato = palabra if not actual else f"{actual} {palabra}"
        if len(candidato) <= ancho:
            actual = candidato
            continue
        if actual:
            lineas.append(actual)
        actual = palabra
    if actual:
        lineas.append(actual)
    return lineas

