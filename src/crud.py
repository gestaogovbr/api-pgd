"""Funções para ler, gravar, atualizar ou apagar dados no banco de dados.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import models, schemas


async def get_plano_trabalho(
    db_session: Session,
    cod_SIAPE_instituidora: int,
    id_plano_trabalho_participante: str,
):
    "Traz um plano de trabalho a partir do banco de dados."
    async for session in db_session:
        result = await session.execute(
            select(models.PlanoTrabalho)
            .filter_by(cod_SIAPE_instituidora=cod_SIAPE_instituidora)
            .filter_by(id_plano_trabalho_participante=id_plano_trabalho_participante)
        )
        db_plano_trabalho = result.unique().scalar_one_or_none()
    if db_plano_trabalho:
        return db_plano_trabalho
    return None


async def create_plano_trabalho(
    db_session: Session,
    cod_SIAPE_instituidora: int,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
):
    "Cria um plano de trabalho definido pelo cod_plano."

    contribuicoes = [
        models.Contribuicao(**contribuicao.dict())
        for contribuicao in plano_trabalho.contribuicoes
    ]
    consolidacoes = [
        models.Consolidacao(**consolidacao.dict())
        for consolidacao in plano_trabalho.consolidacoes
    ]
    # for a in db_atividades:
    #     a.cod_unidade = cod_unidade
    # plano_trabalho.atividades = db_atividades
    # db_plano_trabalho = models.PlanoTrabalho(
    #     cod_unidade=cod_unidade, **plano_trabalho.dict()
    # )
    # db.add(db_plano_trabalho)
    # db.commit()
    # db.refresh(db_plano_trabalho)
    # return schemas.PlanoTrabalhoSchema.from_orm(db_plano_trabalho)


async def update_plano_trabalho(
    db_session: Session,
    cod_SIAPE_instituidora: int,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
):
    "Atualiza um plano de trabalho definido pelo cod_plano."

    # db_plano_trabalho = (
    #     db.query(models.PlanoTrabalho)
    #     .filter(models.PlanoTrabalho.cod_plano == plano_trabalho.cod_plano)
    #     .filter(models.PlanoTrabalho.cod_unidade == cod_unidade)
    #     .first()
    # )
    # # db_plano_trabalho.cod_unidade = cod_unidade
    # for k, _ in plano_trabalho.__dict__.items():
    #     if k[0] != "_" and k != "atividades":
    #         setattr(db_plano_trabalho, k, getattr(plano_trabalho, k))
    # for atividade in db_plano_trabalho.atividades:
    #     db.delete(atividade)
    # db.commit()
    # sa_atividades = [
    #     models.Atividade(cod_unidade=cod_unidade, **a.dict())
    #     for a in plano_trabalho.atividades
    # ]
    # for atividade in sa_atividades:
    #     db_plano_trabalho.atividades.append(atividade)
    # db.commit()
    # db.refresh(db_plano_trabalho)
    # return db_plano_trabalho


async def get_plano_entrega(
    db_session: Session,
    cod_SIAPE_instituidora: int,
    id_plano_entrega_unidade: int,
):
    "Traz um plano de entregas a partir do banco de dados."
    async for session in db_session:
        result = await session.execute(
            select(models.PlanoEntregas)
            .filter_by(cod_SIAPE_instituidora=cod_SIAPE_instituidora)
            .filter_by(id_plano_entrega_unidade=id_plano_entrega_unidade)
        )
        db_plano_entrega = result.unique().scalar_one_or_none()
    if db_plano_entrega:
        return db_plano_entrega
    return None


# The following methods are only for test in CI/CD environment

async def truncate_plano_trabalho(
    db_session: Session,
):
    """Apaga a tabela plano_trabalho.
    Usado no ambiente de testes de integração contínua.
    """
    async for session in db_session:
        result = await session.execute(text("TRUNCATE plano_trabalho CASCADE;"))
        await session.commit()
        return result
