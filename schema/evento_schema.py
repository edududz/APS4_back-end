from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import Optional

class EventoBase(BaseModel):
    titulo: str = Field(..., min_length=1, description="O título do evento não pode ser vazio")
    descricao: str = Field(..., min_length=1, description="Descrição do evento")
    data: date = Field(..., description="Data de realização")
    horario: str = Field(..., min_length=1, description="Horário de realização")
    local: str = Field(..., min_length=1, description="Local do evento")
    capacidade: int = Field(..., gt=0, description="A capacidade do evento deve ser maior que zero")
    categoria: str = Field(..., min_length=1, description="Categoria do evento")

class EventoCreate(EventoBase):
    pass

class EventoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1)
    descricao: Optional[str] = Field(None, min_length=1)
    data: Optional[date] = None
    horario: Optional[str] = Field(None, min_length=1)
    local: Optional[str] = Field(None, min_length=1)
    capacidade: Optional[int] = Field(None, gt=0)
    categoria: Optional[str] = Field(None, min_length=1)

class EventoResponse(EventoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

