from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schema.evento_schema import EventoCreate, EventoUpdate, EventoResponse
from service.evento_service import EventoService
from security.security import require_admin, get_current_user
from model.usuario import Usuario

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.post("/", response_model=EventoResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_evento(
    evento_in: EventoCreate,
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(require_admin)
):
    """Cadastro de evento: Restrito a Administradores (403 se usuário comum, 401 se não autenticado)."""
    return EventoService.cadastrar_evento(db, evento_in)

@router.get("/", response_model=List[EventoResponse])
def listar_eventos(db: Session = Depends(get_db)):
    """Consulta de eventos disponíveis (público / usuários)."""
    return EventoService.listar_eventos(db)

@router.get("/{id}", response_model=EventoResponse)
def consultar_evento(id: int, db: Session = Depends(get_db)):
    """Consulta de detalhes de um evento específico."""
    return EventoService.consultar_evento(db, id)

@router.put("/{id}", response_model=EventoResponse)
def atualizar_evento(
    id: int,
    evento_in: EventoUpdate,
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(require_admin)
):
    """Atualização de evento: Restrito a Administradores."""
    return EventoService.atualizar_evento(db, id, evento_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_evento(
    id: int,
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(require_admin)
):
    """Exclusão de evento: Restrito a Administradores."""
    EventoService.excluir_evento(db, id)
