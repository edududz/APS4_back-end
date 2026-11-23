from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schema.participante_schema import ParticipanteResponse
from schema.inscricao_schema import MensagemSucesso
from service.inscricao_service import InscricaoService
from security.security import get_current_user
from model.usuario import Usuario

router = APIRouter(prefix="/eventos", tags=["Inscrições"])

@router.post(
    "/{evento_id}/inscricoes/{participante_id}",
    response_model=MensagemSucesso,
    status_code=status.HTTP_201_CREATED
)
def inscrever_participante(
    evento_id: int,
    participante_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Inscrição de participante em evento: Exige usuário autenticado (comum ou administrador)."""
    return InscricaoService.inscrever_em_evento(db, evento_id, participante_id)

@router.get(
    "/{evento_id}/inscricoes",
    response_model=List[ParticipanteResponse]
)
def listar_inscritos(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Consulta de participantes inscritos no evento: Exige autenticação."""
    return InscricaoService.listar_inscritos_evento(db, evento_id)
