import io

import docx
import pytest
from fastapi.testclient import TestClient

from main import MAX_BYTES, app

client = TestClient(app)


def docx_vacio():
    buf = io.BytesIO()
    docx.Document().save(buf)
    return buf.getvalue()


@pytest.mark.parametrize("nombre, datos, codigo", [
    ("q.txt", b"hola", 400),
    ("q.docx", b"", 400),
    ("q.pdf", b"x" * (MAX_BYTES + 1), 413),
    ("q.docx", b"esto no es un docx", 400),
    ("q.docx", docx_vacio(), 422),
])
def test_archivo_invalido(nombre, datos, codigo):
    r = client.post("/extract", files={"file": (nombre, datos)})
    assert r.status_code == codigo
    assert r.json()["detail"]
