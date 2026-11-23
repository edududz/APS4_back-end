from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from model.evento import Evento
from model.participante import Participante
from model.inscricao import Inscricao

class RelatorioService:
    @staticmethod
    def relatorio_ocupacao_eventos(db: Session) -> List[Dict[str, Any]]:
        """
        Consolida a ocupação de cada evento cadastrado:
        - Total de inscritos
        - Vagas restantes
        - Percentual de ocupação
        Considera também eventos sem inscrições e evita divisão por zero.
        """
        # Outerjoin garante que eventos sem inscrições sejam retornados com contagem 0
        registros = (
            db.query(
                Evento.id.label("evento_id"),
                Evento.titulo.label("titulo"),
                Evento.capacidade.label("capacidade"),
                func.count(Inscricao.id).label("total_inscritos")
            )
            .outerjoin(Inscricao, Evento.id == Inscricao.evento_id)
            .group_by(Evento.id, Evento.titulo, Evento.capacidade)
            .order_by(Evento.id)
            .all()
        )

        resultado = []
        for reg in registros:
            total_inscritos = int(reg.total_inscritos)
            capacidade = int(reg.capacidade)
            vagas_restantes = max(0, capacidade - total_inscritos)
            percentual = round((total_inscritos / capacidade) * 100, 2) if capacidade > 0 else 0.0

            resultado.append({
                "evento_id": reg.evento_id,
                "titulo": reg.titulo,
                "capacidade": capacidade,
                "total_inscritos": total_inscritos,
                "vagas_disponiveis": vagas_restantes,
                "percentual_ocupacao": percentual
            })

        return resultado

    @staticmethod
    def relatorio_eventos_por_categoria(db: Session) -> List[Dict[str, Any]]:
        """
        Consolida os eventos por categoria:
        - Categoria
        - Quantidade de eventos cadastrados
        - Capacidade total dos eventos da categoria
        - Quantidade total de inscrições nesses eventos
        Utiliza subquery para calcular as inscrições por evento, evitando multiplicação de linhas.
        """
        # Subquery para contagem de inscrições por evento
        subquery_inscricoes = (
            db.query(
                Inscricao.evento_id,
                func.count(Inscricao.id).label("total_inscricoes_evento")
            )
            .group_by(Inscricao.evento_id)
            .subquery()
        )

        registros = (
            db.query(
                Evento.categoria.label("categoria"),
                func.count(Evento.id).label("total_eventos"),
                func.coalesce(func.sum(Evento.capacidade), 0).label("capacidade_total"),
                func.coalesce(func.sum(subquery_inscricoes.c.total_inscricoes_evento), 0).label("total_inscricoes")
            )
            .outerjoin(subquery_inscricoes, Evento.id == subquery_inscricoes.c.evento_id)
            .group_by(Evento.categoria)
            .order_by(Evento.categoria)
            .all()
        )

        resultado = []
        for reg in registros:
            resultado.append({
                "categoria": reg.categoria,
                "total_eventos": int(reg.total_eventos),
                "capacidade_total": int(reg.capacidade_total),
                "total_inscricoes": int(reg.total_inscricoes)
            })

        return resultado

    @staticmethod
    def relatorio_participacao_por_curso(db: Session) -> List[Dict[str, Any]]:
        """
        Consolida as inscrições por curso dos participantes:
        - Nome do curso
        - Quantidade de participantes únicos cadastrados no curso
        - Quantidade total de inscrições realizadas por participantes do curso
        Utiliza COUNT(DISTINCT) para garantir que um participante não seja contado mais de uma vez.
        """
        registros = (
            db.query(
                Participante.curso.label("curso"),
                func.count(distinct(Participante.id)).label("total_participantes"),
                func.count(Inscricao.id).label("total_inscricoes")
            )
            .outerjoin(Inscricao, Participante.id == Inscricao.participante_id)
            .group_by(Participante.curso)
            .order_by(Participante.curso)
            .all()
        )

        resultado = []
        for reg in registros:
            resultado.append({
                "curso": reg.curso,
                "total_participantes": int(reg.total_participantes),
                "total_inscricoes": int(reg.total_inscricoes)
            })

        return resultado

