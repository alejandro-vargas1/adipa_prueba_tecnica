import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from llm import extract_items
from parsers import EXTENSIONES, extract_text
from schemas import Cuestionario

MAX_BYTES = 5 * 1024 * 1024
MAX_CHARS = 30_000

app = FastAPI(title="Extractor de cuestionarios")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

FORMATO_INESPERADO = "No se pudo interpretar el documento"


@app.post("/extract", response_model=Cuestionario)
async def extract(file: UploadFile):
    nombre = file.filename or ""
    if Path(nombre).suffix.lower() not in EXTENSIONES:
        raise HTTPException(400, "Formato no soportado. Usa PDF, DOCX o XLSX")
    datos = await file.read()
    if not datos:
        raise HTTPException(400, "El archivo está vacío")
    if len(datos) > MAX_BYTES:
        raise HTTPException(413, "El documento es demasiado grande")
    try:
        texto = extract_text(nombre, datos)
    except Exception:  # cada librería lanza algo distinto ante un archivo dañado o renombrado
        raise HTTPException(400, "No se pudo leer el archivo")
    if not texto:
        raise HTTPException(422, "No se encontró texto en el documento")
    if len(texto) > MAX_CHARS:
        raise HTTPException(413, "El documento es demasiado grande")

    try:
        data = await extract_items(texto)
    except json.JSONDecodeError:
        raise HTTPException(502, FORMATO_INESPERADO)
    except Exception:  # key inválida, límite 429, timeout o servicio caído
        raise HTTPException(502, "El servicio de extracción no está disponible, intenta de nuevo")

    try:
        if not data["items"]:
            raise HTTPException(422, "No se detectaron ítems en el documento")
        # el número y el total los calcula el código, no el LLM; antes de validar
        for i, item in enumerate(data["items"], 1):
            item["numero"] = i
        data["total_items"] = len(data["items"])
        return Cuestionario.model_validate(data)
    except (KeyError, TypeError, ValidationError):
        raise HTTPException(502, FORMATO_INESPERADO)
