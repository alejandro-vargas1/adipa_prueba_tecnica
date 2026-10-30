import copy
from pathlib import Path

from fastapi.testclient import TestClient

import main
from llm import EJEMPLO

client = TestClient(main.app)
EJEMPLO_DOCX = Path(__file__).parents[2] / "examples" / "cuestionario_it.docx"


def subir_con_llm(monkeypatch, respuesta):
    async def falso(texto):
        return respuesta
    monkeypatch.setattr(main, "extract_items", falso)  # sin llamar a Gemini
    return client.post("/extract", files={"file": ("q.docx", EJEMPLO_DOCX.read_bytes())})


def test_corrige_numeracion_y_total(monkeypatch):
    data = copy.deepcopy(EJEMPLO)
    data["total_items"] = 7
    for item in data["items"]:
        item["numero"] = 9
    r = subir_con_llm(monkeypatch, data)
    assert r.status_code == 200
    assert r.json()["total_items"] == 3
    assert [i["numero"] for i in r.json()["items"]] == [1, 2, 3]


def test_sin_items_devuelve_422(monkeypatch):
    r = subir_con_llm(monkeypatch, {**EJEMPLO, "items": []})
    assert r.status_code == 422
