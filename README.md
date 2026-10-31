# Extractor de cuestionarios

Sube un PDF, DOCX o XLSX con un cuestionario y recibe sus ítems, alternativas, respuesta correcta e idioma en un
JSON estandarizado.

**Demo:** Frontend: https://adipa-frontend-pt6w.onrender.com · API: https://adipa-backend.onrender.com
(`/docs` para Swagger)

> El backend corre en el plan gratuito de Render: si estaba inactivo, la primera petición puede tardar hasta un minuto.

## Cómo funciona

```
archivo ──► main.py ──► parsers.py ──► llm.py ──► main.py ──► schemas.py ──► JSON
            valida      texto plano    Gemini     numera y    Pydantic
            el archivo                 (JSON)     cuenta      valida
```

1. **`main.py`** valida el archivo antes de leerlo: extensión PDF, DOCX o XLSX (400), que no esté vacío (400) y que
   pese como máximo 5 MB (413).
2. **`parsers.py`** convierte el archivo en texto: pdfplumber (PDF), python-docx (párrafos y tablas en su orden,
   negrita como `**texto**`) y openpyxl (cada fila como `celda | celda | ...`). Después `main.py` comprueba que se
   pudo leer (400 si está dañado o renombrado), que tiene texto (422, p. ej. un PDF escaneado) y que no pasa de
   30.000 caracteres (413).
3. **`llm.py`** manda el texto a Gemini con un prompt fijo (los 5 tipos, las reglas de valores y el JSON de ejemplo
   del enunciado), temperatura 0 y salida JSON.
4. **`main.py`** renumera los ítems y recalcula `total_items`: eso lo hace el código, no el LLM.
5. **`schemas.py`** valida el resultado con Pydantic: tipos permitidos, que un ítem de desarrollo no tenga
   alternativas, que `respuesta_correcta` exista entre las alternativas y que el idioma sea un código de 2 letras.

El LLM propone y Pydantic decide: nada llega al usuario sin pasar por el esquema.

```
backend/
  main.py          # FastAPI: POST /extract, validación del archivo y errores
  parsers.py       # archivo -> texto
  llm.py           # texto -> dict (Gemini)
  schemas.py       # Cuestionario, Item, Alternativa
  tests/
  Dockerfile
frontend/          # React + Vite, un componente (src/App.jsx); Dockerfile con build + nginx
examples/          # cuestionarios inventados y sus JSON resultantes
docker-compose.yml # levanta backend y frontend en local
```

## Correr en local

Requisitos: Docker y una API key de Gemini.

```bash
cp .env.example .env          # y completa GEMINI_API_KEY
docker compose up --build
```

Frontend en http://localhost:5173 y API en http://localhost:8000 (imágenes `adipa_frontend` y `adipa_backend`).
Para detenerlo: `Ctrl + C` o `docker compose down`.

> `docker-compose.yml` es solo para probar en local. En producción cada servicio se despliega por separado en
> Render (ver [Deploy](#deploy-render)).

## Variables de entorno

| Variable | Dónde | Para qué |
|---|---|---|
| `GEMINI_API_KEY` | Backend | Key gratuita de [Google AI Studio](https://aistudio.google.com/apikey) |
| `VITE_API_URL` | Frontend | URL del backend, sin `/` al final. Por defecto `http://localhost:8000`. Con docker compose se lee al arrancar el contenedor; en Render, al hacer el build (si cambia, hay que redesplegar el frontend) |
| `PORT` | Backend | Puerto de uvicorn. Por defecto `8000`; en Render lo asigna la plataforma |

El `.env` va en la raíz del repo y está en `.gitignore`. Solo se sube `.env.example`.

## API

`POST /extract`, multipart con el campo `file`:

```bash
curl -F file=@examples/cuestionario_it.docx localhost:8000/extract
```

| Código | Cuándo |
|---|---|
| 200 | JSON del cuestionario (ver `examples/*.json`) |
| 400 | Formato no soportado, archivo vacío o dañado |
| 413 | Más de 5 MB o más de 30.000 caracteres de texto |
| 422 | El documento no tiene texto (p. ej. PDF escaneado) o no se detectaron ítems |
| 502 | Gemini no responde (key, límite de peticiones, caída) o devolvió un JSON que no cumple el esquema |

Todos los errores traen un mensaje en español en `detail`, que es el que muestra el frontend.

## Tests

```bash
docker compose run --rm -v ./examples:/examples backend python -m pytest
```

El volumen hace falta porque `test_endpoint.py` usa `examples/cuestionario_it.docx`, que no está dentro de la imagen.

- `test_validation.py`: archivo `.txt`, vacío, de más de 5 MB, dañado y sin texto, cada uno con su código.
- `test_schema.py`: el JSON del enunciado pasa; respuestas fuera de las alternativas, tipo inexistente, desarrollo
  con alternativas, `total_items` incoherente e idioma mal escrito fallan.
- `test_endpoint.py`: flujo completo con Gemini reemplazado por `monkeypatch` (no gasta cuota): corrige numeración y
  total, y devuelve 422 si no hay ítems.

## Ejemplos

Cuestionarios inventados y la respuesta real de la API para cada uno:

| Archivo | Idioma | Tipos que incluye |
|---|---|---|
| `cuestionario_es.pdf` | Español | Likert, selección múltiple, verdadero/falso, desarrollo |
| `cuestionario_it.docx` | Italiano | Likert, selección múltiple (respuesta en negrita), emparejamiento (tabla), desarrollo |
| `cuestionario_en.xlsx` | Inglés | Likert, selección múltiple, verdadero/falso, desarrollo |

## Deploy (Render)

**Backend (Web Service)**

1. New → Web Service → conectar este repo.
2. Root Directory: `backend`. Render detecta el `Dockerfile` y usa Language: Docker, así que no hace falta comando
   de build ni de start (uvicorn escucha en el `PORT` que asigna Render).
3. Instance Type: Free.
4. Environment: `GEMINI_API_KEY`.

**Frontend (Static Site)**

1. New → Static Site → conectar este repo.
2. Root Directory: `frontend`.
3. Build: `npm install && npm run build`
4. Publish Directory: `dist`
5. Environment: `VITE_API_URL` = URL del backend.

## Supuestos

- **Valores de las alternativas:** Likert con enteros desde 0, en el orden de la escala; selección múltiple con
  letras mayúsculas aunque el documento use "a)"; verdadero/falso con `"V"` y `"F"`.
- **Nombres de tipo:** el enunciado solo muestra `escala_likert`, `seleccion_multiple` y `desarrollo`;
  `verdadero_falso` y `emparejamiento` siguen el mismo estilo.
- **Emparejamiento:** la columna izquierda va en el enunciado, la derecha como alternativas, y la respuesta es un
  objeto `{"1": "B", "2": "A"}`.
- **Respuesta correcta:** solo si el documento la indica (texto, columna, marca o negrita); si no, `null`.
- **Idioma:** código ISO 639-1 de 2 letras, detectado por el mismo LLM.
- **`numero` y `total_items`:** los calcula el código, para no depender de que el LLM cuente bien.
- **Límites:** 5 MB por archivo y 30.000 caracteres de texto extraído (una sola llamada al LLM).
- **Modelo:** `gemini-3.5-flash-lite`, gratuito. Se eligió porque respeta `temperature=0`; los modelos 3.6 o
  superiores la ignoran.
