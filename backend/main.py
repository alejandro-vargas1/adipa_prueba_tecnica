from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from parsers import EXTENSIONES, extract_text
from schemas import Cuestionario

MAX_BYTES = 5 * 1024 * 1024
MAX_CHARS = 30_000

app = FastAPI(title="Extractor de cuestionarios")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Respuesta fija del enunciado hasta conectar parsers y LLM (bloques 2 y 3).
EJEMPLO = {
    "titulo": "Questionario di esempio",
    "idioma": "it",
    "total_items": 3,
    "items": [
        {
            "numero": 1,
            "enunciado": "Mi preoccupo eccessivamente per cose di poca importanza.",
            "tipo": "escala_likert",
            "alternativas": [
                {"valor": 0, "texto": "Mai"},
                {"valor": 1, "texto": "A volte"},
                {"valor": 2, "texto": "Spesso"},
                {"valor": 3, "texto": "Sempre"},
            ],
            "respuesta_correcta": None,
        },
        {
            "numero": 2,
            "enunciado": "Quale numero completa la serie: 2, 4, 8, 16, ...?",
            "tipo": "seleccion_multiple",
            "alternativas": [
                {"valor": "A", "texto": "18"},
                {"valor": "B", "texto": "24"},
                {"valor": "C", "texto": "32"},
            ],
            "respuesta_correcta": "C",
        },
        {
            "numero": 3,
            "enunciado": "Descriva una situazione recente in cui si è sentito sotto pressione.",
            "tipo": "desarrollo",
            "alternativas": [],
            "respuesta_correcta": None,
        },
    ],
}


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
    # el texto se usará con el LLM en el bloque 3
    return Cuestionario.model_validate(EJEMPLO)
