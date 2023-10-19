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
    db_plano_trabalho = models.PlanoTrabalho(
        **plano_trabalho.model_dump()
    )
    async for session in db_session:
        # for contribuicao in contribuicoes:
        #     await session.add(contribuicao)
        #     db_plano_trabalho.contribuicoes.append(contribuicao)
        # # db_plano_trabalho.contribuicoes = contribuicoes
        # for consolidacao in consolidacoes:
        #     await session.add(consolidacao)
        #     db_plano_trabalho.consolidacoes.append(consolidacao)
        await session.add(db_plano_trabalho)
        await session.commit()
    # db_plano_trabalho.consolidacoes = consolidacoes
    # db_session.refresh(db_plano_trabalho)
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


async def get_status_participante(
    db_session: Session,
    cod_SIAPE_instituidora: int,
    cpf_participante: str,
):
    "Traz os status do participante a partir do banco de dados."
    async for session in db_session:
        result = await session.execute(
            select(models.StatusParticipante)
            .filter_by(cpf_participante=cpf_participante)
        )
        db_status_participante = result.all()
    if db_status_participante:
        return db_status_participante
    return None

async def create_status_participante(
    db_session: Session,
    status_participante: schemas.StatusParticipanteSchema,
):
    """Cria um status de participante definido pelos dados do schema Pydantic
    status_participante.
    TODO: Possibilitar inserir mais de um registro
    """

    db_status_participante = models.StatusParticipante(
        **status_participante.model_dump()
    )
    async for session in db_session:
        session.add(db_status_participante)
        await session.commit()


# The following methods are only for test in CI/CD environment

async def truncate_plano_entregas(
    db_session: Session,
):
    """Apaga a tabela plano_entregas.
    Usado no ambiente de testes de integração contínua.
    """
    async for session in db_session:
        result = await session.execute(text("TRUNCATE plano_entregas CASCADE;"))
        await session.commit()
        return result

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

async def truncate_status_participante(
    db_session: Session,
):
    """Apaga a tabela status_participante.
    Usado no ambiente de testes de integração contínua.
    """
    async for session in db_session:
        result = await session.execute(text("TRUNCATE status_participante CASCADE;"))
        await session.commit()
        return result