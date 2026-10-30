import io
from pathlib import Path

import docx
import openpyxl
import pdfplumber
from docx.table import Table

EXTENSIONES = {".pdf", ".docx", ".xlsx"}


def extract_text(nombre: str, datos: bytes) -> str:
    lector = {".pdf": _pdf, ".docx": _docx, ".xlsx": _xlsx}[Path(nombre).suffix.lower()]
    return lector(io.BytesIO(datos)).strip()


def _pdf(archivo) -> str:
    with pdfplumber.open(archivo) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def _docx(archivo) -> str:
    lineas = []
    # en orden del documento: una tabla puede estar en medio de un ítem (emparejamiento)
    for bloque in docx.Document(archivo).iter_inner_content():
        if isinstance(bloque, Table):
            lineas += [" | ".join(c.text for c in fila.cells) for fila in bloque.rows]
        else:
            # la negrita a veces marca la respuesta correcta
            lineas.append("".join(f"**{r.text}**" if r.bold and r.text.strip() else r.text for r in bloque.runs))
    return "\n".join(lineas)


def _xlsx(archivo) -> str:
    libro = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
    try:
        return "\n".join(
            " | ".join(str(c) for c in fila if c is not None)
            for hoja in libro
            for fila in hoja.iter_rows(values_only=True)
        )
    finally:
        libro.close()
