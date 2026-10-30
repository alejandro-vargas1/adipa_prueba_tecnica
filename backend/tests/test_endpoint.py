from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from schemas import Cuestionario

client = TestClient(app)
EJEMPLO_DOCX = Path(__file__).parents[2] / "examples" / "cuestionario_it.docx"


def test_extract_devuelve_cuestionario():
    r = client.post("/extract", files={"file": ("q.docx", EJEMPLO_DOCX.read_bytes())})
    assert r.status_code == 200
    Cuestionario.model_validate(r.json())
