from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional

class ParticipanteBase(BaseModel):
    nome: str = Field(..., min_length=1, description="O nome do participante não pode ser vazio")
    email: EmailStr = Field(..., description="O e-mail deve possuir formato válido")
    curso: str = Field(..., min_length=1, description="Curso ao qual pertence")

class ParticipanteCreate(ParticipanteBase):
    pass

class ParticipanteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    curso: Optional[str] = Field(None, min_length=1)

class ParticipanteResponse(ParticipanteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

