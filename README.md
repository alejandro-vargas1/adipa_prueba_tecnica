# Extractor de cuestionarios

Sube un PDF, DOCX o XLSX con un cuestionario y recibe sus ítems en JSON.

## Correr en local

```bash
cd backend
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
set -a; . ../.env; set +a   # carga GEMINI_API_KEY
.venv/bin/uvicorn main:app --reload
curl -F file=@../examples/cuestionario_it.docx localhost:8000/extract
```

Frontend (con el backend corriendo en `localhost:8000`):

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Variables de entorno: ver `.env.example`.

## Deploy del backend (Render)

1. New → Web Service → conectar este repo.
2. Root Directory: `backend`. La versión de Python se toma de `backend/.python-version`.
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Environment: `GEMINI_API_KEY`.

## Deploy del frontend (Render, Static Site)

1. New → Static Site → conectar este repo.
2. Root Directory: `frontend`.
3. Build: `npm install && npm run build`
4. Publish Directory: `dist`
5. Environment: `VITE_API_URL` = URL del backend (se usa al hacer el build).
