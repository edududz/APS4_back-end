from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schema.participante_schema import ParticipanteCreate, ParticipanteUpdate, ParticipanteResponse
from service.participante_service import ParticipanteService
from security.security import require_admin, get_current_user
from model.usuario import Usuario

router = APIRouter(prefix="/participantes", tags=["Participantes"])

@router.post("/", response_model=ParticipanteResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_participante(
    participante_in: ParticipanteCreate,
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(require_admin)
):
    """Cadastro de participante: Exige autenticação administrativa."""
    return ParticipanteService.cadastrar_participante(db, participante_in)

@router.get("/", response_model=List[ParticipanteResponse])
def listar_participantes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Consulta de participantes: Exige usuário autenticado."""
    return ParticipanteService.listar_participantes(db)

@router.get("/{id}", response_model=ParticipanteResponse)
def consultar_participante(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Consulta de participante específico: Exige usuário autenticado."""
    return ParticipanteService.consultar_participante(db, id)

@router.put("/{id}", response_model=ParticipanteResponse)
def atualizar_participante(
    id: int,
    participante_in: ParticipanteUpdate,
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(require_admin)
):
    """Atualização de participante: Restrito a Administradores."""
    return ParticipanteService.atualizar_participante(db, id, participante_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_participante(
    id: int,
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(require_admin)
):
    """Exclusão de participante: Restrito a Administradores."""
    ParticipanteService.excluir_participante(db, id)
