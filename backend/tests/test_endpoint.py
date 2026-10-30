from fastapi.testclient import TestClient

from main import app
from schemas import Cuestionario

client = TestClient(app)


def test_extract_devuelve_cuestionario():
    r = client.post("/extract", files={"file": ("q.docx", b"contenido")})
    assert r.status_code == 200
    Cuestionario.model_validate(r.json())
