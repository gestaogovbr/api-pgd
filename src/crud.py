"""Funções para ler, gravar, atualizar ou apagar dados no banco de dados.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.sql import text

import models, schemas
from db_config import DbContextManager, SyncSession


async def get_plano_trabalho(
    db_session: DbContextManager,
    cod_SIAPE_instituidora: int,
    id_plano_trabalho_participante: str,
):
    "Traz um plano de trabalho a partir do banco de dados."
    async with db_session as session:
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
    db_session: DbContextManager,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
):
    """Cria um plano de trabalho definido pelos dados do schema Pydantic
    plano_trabalho.
    """
    contribuicoes = [
        models.Contribuicao(**contribuicao.model_dump())
        for contribuicao in plano_trabalho.contribuicoes
    ]
    consolidacoes = [
        models.Consolidacao(**consolidacao.model_dump())
        for consolidacao in plano_trabalho.consolidacoes
    ]
    plano_trabalho.contribuicoes = []
    plano_trabalho.consolidacoes = []
    db_plano_trabalho = models.PlanoTrabalho(**plano_trabalho.model_dump())
    db_plano_trabalho.data_insercao = datetime.now()
    async with db_session as session:
        for contribuicao in contribuicoes:
            session.add(contribuicao)
            db_plano_trabalho.contribuicoes.append(contribuicao)
            db_plano_trabalho.contribuicoes = contribuicoes
        for consolidacao in consolidacoes:
            session.add(consolidacao)
            db_plano_trabalho.consolidacoes.append(consolidacao)
        session.add(db_plano_trabalho)
        await session.commit()
        # db_session.refresh(db_plano_trabalho)
    # return schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho)


async def update_plano_trabalho(
    db_session: DbContextManager,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
):
    "Atualiza um plano de trabalho definido pelo cod_plano."
    async with db_session as session:
        result = await session.execute(
            select(models.PlanoTrabalho)
            .filter_by(
                models.PlanoTrabalho.cod_SIAPE_instituidora
                == plano_trabalho["cod_SIAPE_instituidora"]
            )
            .filter_by(
                models.PlanoTrabalho.id_plano_trabalho_participante
                == plano_trabalho["id_plano_trabalho_participante"]
            )
        )
        db_plano_trabalho = result.unique().scalar_one_or_none()
        await session.delete(db_plano_trabalho)
    await create_plano_trabalho(db_session, plano_trabalho)
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
    db_session: DbContextManager,
    cod_SIAPE_instituidora: int,
    id_plano_entrega_unidade: int,
):
    "Traz um plano de entregas a partir do banco de dados."
    async with db_session as session:
        result = await session.execute(
            select(models.PlanoEntregas)
            .filter_by(cod_SIAPE_instituidora=cod_SIAPE_instituidora)
            .filter_by(id_plano_entrega_unidade=id_plano_entrega_unidade)
        )
        db_plano_entrega = result.unique().scalar_one_or_none()
    if db_plano_entrega:
        return db_plano_entrega
    return None


async def get_status_participante(
    db_session: DbContextManager,
    cod_SIAPE_instituidora: int,
    cpf_participante: str,
):
    "Traz os status do participante a partir do banco de dados."
    async with db_session as session:
        result = await session.execute(
            select(models.StatusParticipante)
            .filter_by(cod_SIAPE_instituidora=cod_SIAPE_instituidora)
            .filter_by(cpf_participante=cpf_participante)
        )
        db_status_participante = result.all()
    if db_status_participante:
        return db_status_participante
    return None


async def create_status_participante(
    db_session: DbContextManager,
    status_participante: schemas.StatusParticipanteSchema,
):
    """Cria um status de participante definido pelos dados do schema Pydantic
    status_participante.
    TODO: Possibilitar inserir mais de um registro
    """

    db_status_participante = models.StatusParticipante(
        **status_participante.model_dump()
    )
    async with db_session as session:
        session.add(db_status_participante)
        await session.commit()


# The following methods are only for test in CI/CD environment


def truncate_plano_entregas():
    """Apaga a tabela plano_entregas.
    Usado no ambiente de testes de integração contínua.
    """
    with SyncSession.begin() as session:
        result = session.execute(text("TRUNCATE plano_entregas CASCADE;"))
    return result


def truncate_plano_trabalho():
    """Apaga a tabela plano_trabalho.
    Usado no ambiente de testes de integração contínua.
    """
    with SyncSession.begin() as session:
        result = session.execute(text("TRUNCATE plano_trabalho CASCADE;"))
    return result


def truncate_status_participante():
    """Apaga a tabela status_participante.
    Usado no ambiente de testes de integração contínua.
    """
    with SyncSession.begin() as session:
        result = session.execute(text("TRUNCATE status_participante CASCADE;"))
    return result
