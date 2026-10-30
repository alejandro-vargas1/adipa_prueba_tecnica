from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Tipo(str, Enum):
    escala_likert = "escala_likert"
    seleccion_multiple = "seleccion_multiple"
    verdadero_falso = "verdadero_falso"
    desarrollo = "desarrollo"
    emparejamiento = "emparejamiento"


class Alternativa(BaseModel):
    valor: int | str
    texto: str


class Item(BaseModel):
    numero: int
    enunciado: str
    tipo: Tipo
    alternativas: list[Alternativa]
    respuesta_correcta: int | str | dict[str, str] | None = None

    @model_validator(mode="after")
    def coherente(self):
        if self.tipo == Tipo.desarrollo and self.alternativas:
            raise ValueError("un ítem de desarrollo no tiene alternativas")
        r = self.respuesta_correcta
        if r is None:
            return self
        valores = {a.valor for a in self.alternativas}
        # emparejamiento: {"1": "B"} -> cada letra debe ser una alternativa
        if not set(r.values() if isinstance(r, dict) else [r]) <= valores:
            raise ValueError("respuesta_correcta no está entre las alternativas")
        return self


class Cuestionario(BaseModel):
    titulo: str
    idioma: str = Field(pattern=r"^[a-z]{2}$")
    total_items: int
    items: list[Item]

    @model_validator(mode="after")
    def total_coincide(self):
        if self.total_items != len(self.items):
            raise ValueError("total_items no coincide con el número de ítems")
        return self
