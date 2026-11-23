from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from model.participante import Participante
from schema.participante_schema import ParticipanteCreate, ParticipanteUpdate

class ParticipanteService:
    @staticmethod
    def listar_participantes(db: Session) -> List[Participante]:
        return db.query(Participante).all()

    @staticmethod
    def consultar_participante(db: Session, participante_id: int) -> Participante:
        participante = db.query(Participante).filter(Participante.id == participante_id).first()
        if not participante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participante não encontrado."
            )
        return participante

    @staticmethod
    def cadastrar_participante(db: Session, participante_in: ParticipanteCreate) -> Participante:
        # Verificar duplicidade de e-mail
        existente = db.query(Participante).filter(Participante.email == participante_in.email).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um participante cadastrado com este e-mail."
            )

        novo_participante = Participante(**participante_in.model_dump())
        db.add(novo_participante)
        db.commit()
        db.refresh(novo_participante)
        return novo_participante

    @staticmethod
    def atualizar_participante(db: Session, participante_id: int, participante_in: ParticipanteUpdate) -> Participante:
        participante = ParticipanteService.consultar_participante(db, participante_id)
        dados_atualizacao = participante_in.model_dump(exclude_unset=True)

        if "email" in dados_atualizacao and dados_atualizacao["email"] != participante.email:
            existente = db.query(Participante).filter(
                Participante.email == dados_atualizacao["email"],
                Participante.id != participante_id
            ).first()
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe um participante cadastrado com este e-mail."
                )

        for campo, valor in dados_atualizacao.items():
            setattr(participante, campo, valor)
        db.commit()
        db.refresh(participante)
        return participante

    @staticmethod
    def excluir_participante(db: Session, participante_id: int) -> None:
        participante = ParticipanteService.consultar_participante(db, participante_id)
        db.delete(participante)
        db.commit()
