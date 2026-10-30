import json

from google import genai
from google.genai import types

MODELO = "gemini-3.5-flash-lite"  # gratis y respeta temperature=0 (los 3.6+ la ignoran)

# Ejemplo de salida del enunciado: va al final del prompt.
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

PROMPT = f"""Eres un extractor de cuestionarios. Recibes el texto de un documento y respondes solo con JSON.

Tipos de ítem (campo "tipo"):
- escala_likert: el respondente elige un grado de una escala (nunca/siempre, desacuerdo/acuerdo).
- seleccion_multiple: una pregunta con opciones y una sola correcta.
- verdadero_falso: una afirmación que es verdadera o falsa.
- desarrollo: respuesta abierta, sin alternativas ("alternativas": []).
- emparejamiento: unir cada elemento de una columna con uno de otra.

Reglas de valores:
- escala_likert: "valor" entero desde 0, en el orden de la escala. Si el documento da una escala común
  ("responda usando..."), aplícala a cada ítem Likert.
- seleccion_multiple: "valor" en letras mayúsculas A, B, C... aunque el documento use "a)" o no use letras.
- verdadero_falso: alternativas {{"valor": "V", "texto": ...}} y {{"valor": "F", "texto": ...}} con el texto en
  el idioma del documento.
- emparejamiento: el enunciado incluye los elementos de la columna izquierda numerados; las alternativas son la
  columna derecha con letras; "respuesta_correcta" es un objeto como {{"1": "B", "2": "A"}}.

Reglas generales:
- "respuesta_correcta" solo si el documento la indica (texto como "Respuesta correcta", "Soluzioni", una columna
  "Answer", una marca entre paréntesis o texto en **negrita**). Si no, null. Debe ser un "valor" de las alternativas.
- Copia enunciados y alternativas completos y tal cual, sin traducir, corregir ni acortar (conserva frases como
  "Verdadero o falso:"). Quita solo el número o la letra del ítem y las marcas de respuesta correcta.
- "idioma": código ISO 639-1 de dos letras del idioma del documento.
- "titulo": el título del documento.

Ejemplo de salida:
{json.dumps(EJEMPLO, ensure_ascii=False)}"""


async def extract_items(texto: str) -> dict:
    client = genai.Client()  # lee GEMINI_API_KEY del entorno
    respuesta = await client.aio.models.generate_content(
        model=MODELO,
        contents=texto,
        config=types.GenerateContentConfig(
            system_instruction=PROMPT,
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    return json.loads(respuesta.text)
