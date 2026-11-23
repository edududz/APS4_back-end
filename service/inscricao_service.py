from typing import List
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from model.inscricao import Inscricao
from model.participante import Participante
from service.evento_service import EventoService
from service.participante_service import ParticipanteService

class InscricaoService:
    @staticmethod
    def inscrever_em_evento(db: Session, evento_id: int, participante_id: int):
        # 1. Se o evento existe (retorna 404 se não existir)
        evento = EventoService.consultar_evento(db, evento_id)

        # 2. Se o participante existe (retorna 404 se não existir)
        ParticipanteService.consultar_participante(db, participante_id)

        # 3. Se o participante já está inscrito no evento
        inscricao_existente = db.query(Inscricao).filter(
            Inscricao.evento_id == evento_id,
            Inscricao.participante_id == participante_id
        ).first()
        if inscricao_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Participante já está inscrito neste evento."
            )

        # 4. Se existem vagas disponíveis
        total_inscritos = db.query(Inscricao).filter(Inscricao.evento_id == evento_id).count()
        if total_inscritos >= evento.capacidade:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não existem vagas disponíveis para este evento."
            )

        nova_inscricao = Inscricao(
            evento_id=evento_id,
            participante_id=participante_id,
            data_inscricao=date.today()
        )
        db.add(nova_inscricao)
        db.commit()
        db.refresh(nova_inscricao)
        return {"detail": "Inscrição realizada com sucesso."}

    @staticmethod
    def listar_inscritos_evento(db: Session, evento_id: int) -> List[Participante]:
        # Valida existência do evento (retorna 404 se não existir)
        EventoService.consultar_evento(db, evento_id)

        # Recupera participantes inscritos através do relacionamento no banco
        participantes = (
            db.query(Participante)
            .join(Inscricao, Participante.id == Inscricao.participante_id)
            .filter(Inscricao.evento_id == evento_id)
            .all()
        )
        return participantes

