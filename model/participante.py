from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Participante(Base):
    __tablename__ = "participantes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    curso = Column(String, nullable=False)

    # Relacionamento com Inscrições - cascata para evitar registros órfãos
    inscricoes = relationship(
        "Inscricao",
        back_populates="participante",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
