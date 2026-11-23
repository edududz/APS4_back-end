from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from model.evento import Evento
from model.inscricao import Inscricao
from schema.evento_schema import EventoCreate, EventoUpdate

class EventoService:
    @staticmethod
    def listar_eventos(db: Session) -> List[Evento]:
        return db.query(Evento).all()

    @staticmethod
    def consultar_evento(db: Session, evento_id: int) -> Evento:
        evento = db.query(Evento).filter(Evento.id == evento_id).first()
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado."
            )
        return evento

    @staticmethod
    def cadastrar_evento(db: Session, evento_in: EventoCreate) -> Evento:
        novo_evento = Evento(**evento_in.model_dump())
        db.add(novo_evento)
        db.commit()
        db.refresh(novo_evento)
        return novo_evento

    @staticmethod
    def atualizar_evento(db: Session, evento_id: int, evento_in: EventoUpdate) -> Evento:
        evento = EventoService.consultar_evento(db, evento_id)
        dados_atualizacao = evento_in.model_dump(exclude_unset=True)
        for campo, valor in dados_atualizacao.items():
            setattr(evento, campo, valor)
        db.commit()
        db.refresh(evento)
        return evento

    @staticmethod
    def excluir_evento(db: Session, evento_id: int) -> None:
        evento = EventoService.consultar_evento(db, evento_id)
        db.delete(evento)
        db.commit()

    @staticmethod
    def verificar_vagas(db: Session, evento_id: int) -> bool:
        evento = EventoService.consultar_evento(db, evento_id)
        total_inscritos = db.query(Inscricao).filter(Inscricao.evento_id == evento_id).count()
        return total_inscritos < evento.capacidade
