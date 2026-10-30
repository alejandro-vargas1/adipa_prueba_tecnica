from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from schemas import Cuestionario

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
    return Cuestionario.model_validate(EJEMPLO)
