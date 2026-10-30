# Extractor de cuestionarios

Sube un PDF, DOCX o XLSX con un cuestionario y recibe sus ítems, alternativas, respuesta correcta e idioma en un
JSON estandarizado.

**Demo:** Frontend: _pendiente_ · API: _pendiente_ (`/docs` para Swagger)

> El backend corre en el plan gratuito de Render: si estaba inactivo, la primera petición puede tardar hasta un minuto.

## Cómo funciona

```
archivo ──► parsers.py ──► llm.py ──► main.py ──► schemas.py ──► JSON
            texto plano    Gemini     numera y    Pydantic
                           (JSON)     cuenta      valida
```

1. **`parsers.py`** convierte el archivo en texto: pdfplumber (PDF), python-docx (párrafos y tablas en su orden,
   negrita como `**texto**`) y openpyxl (cada fila como `celda | celda | ...`).
2. **`llm.py`** manda el texto a Gemini con un prompt fijo (los 5 tipos, las reglas de valores y el JSON de ejemplo
   del enunciado), temperatura 0 y salida JSON.
3. **`main.py`** renumera los ítems y recalcula `total_items`: eso lo hace el código, no el LLM.
4. **`schemas.py`** valida el resultado con Pydantic: tipos permitidos, que un ítem de desarrollo no tenga
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
docker-compose.yml # levanta backend y frontend
```

## Correr en local

### Con Docker (recomendado)

Requisitos: Docker y una API key de Gemini.

```bash
cp .env.example .env          # y completa GEMINI_API_KEY
docker compose up --build
```

Frontend en http://localhost:5173 y API en http://localhost:8000 (imágenes `adipa_frontend` y `adipa_backend`).
Para detenerlo: `Ctrl + C` o `docker compose down`.

### Sin Docker

Requisitos: Python 3.13, Node 20.19+ o 22.12+ y una API key de Gemini.

```bash
cp .env.example .env          # y completa GEMINI_API_KEY

# Terminal 1: backend en http://localhost:8000
cd backend
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
set -a; . ../.env; set +a     # carga GEMINI_API_KEY
.venv/bin/uvicorn main:app --reload

# Terminal 2: frontend en http://localhost:5173
cd frontend
npm install
npm run dev
```

## Variables de entorno

| Variable | Dónde | Para qué |
|---|---|---|
| `GEMINI_API_KEY` | Backend | Key gratuita de [Google AI Studio](https://aistudio.google.com/apikey) |
| `VITE_API_URL` | Frontend | URL del backend. Por defecto `http://localhost:8000`. En el contenedor se lee al arrancar; sin Docker (`npm run build`, Render), al hacer el build |
| `PORT` | Backend, solo en el contenedor | Puerto de uvicorn. Por defecto `8000`; lo asignan plataformas como Railway o Cloud Run |

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
cd backend && .venv/bin/python -m pytest
```

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
2. Root Directory: `backend`. La versión de Python se toma de `backend/.python-version`.
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Environment: `GEMINI_API_KEY`.

**Frontend (Static Site)**

1. New → Static Site → conectar este repo.
2. Root Directory: `frontend`.
3. Build: `npm install && npm run build`
4. Publish Directory: `dist`
5. Environment: `VITE_API_URL` = URL del backend.

## Deploy con Docker (cualquier plataforma)

Las imágenes no llevan URLs ni keys dentro: todo se pasa como variable de entorno al arrancar.

```bash
docker build -t adipa_backend ./backend
docker build -t adipa_frontend ./frontend

docker run -p 8000:8000 -e GEMINI_API_KEY=... adipa_backend
docker run -p 80:80 -e VITE_API_URL=https://api.midominio.com adipa_frontend
```

El frontend sirve con nginx en el puerto 80. Al arrancar escribe `VITE_API_URL` en `config.js`, así que la misma
imagen sirve para cualquier backend sin reconstruirla.

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
