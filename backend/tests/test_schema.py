import copy

import pytest
from pydantic import ValidationError

from main import EJEMPLO
from schemas import Cuestionario


def variante(**cambios_item2):
    data = copy.deepcopy(EJEMPLO)
    data["items"][1].update(cambios_item2)
    return data


def test_json_valido_pasa():
    assert Cuestionario.model_validate(EJEMPLO).total_items == 3


def test_emparejamiento_valido_pasa():
    data = variante(tipo="emparejamiento", respuesta_correcta={"1": "C", "2": "A"})
    Cuestionario.model_validate(data)


@pytest.mark.parametrize("data", [
    variante(respuesta_correcta="D"),
    variante(tipo="emparejamiento", respuesta_correcta={"1": "Z"}),
    variante(tipo="ensayo"),
    variante(tipo="desarrollo"),
    {**EJEMPLO, "total_items": 5},
    {**EJEMPLO, "idioma": "italiano"},
])
def test_json_invalido_falla(data):
    with pytest.raises(ValidationError):
        Cuestionario.model_validate(data)
