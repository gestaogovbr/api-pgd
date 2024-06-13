"""Funções para ler, gravar, atualizar ou apagar dados no banco de dados.
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, and_, func
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

import models, schemas
from db_config import DbContextManager, SyncSession


async def get_plano_trabalho(
    db_session: DbContextManager,
    cod_SIAPE_instituidora: int,
    id_plano_trabalho_participante: str,
) -> Optional[schemas.PlanoTrabalhoSchema]:
    """Traz um plano de trabalho a partir do banco de dados, consultando
    a partir dos parâmetros informados.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        cod_SIAPE_instituidora (int): Código SIAPE da unidade instituidora.
        id_plano_trabalho_participante (str): id do Plano de Trabalho do
            participante.

    Returns:
        Optional[schemas.PlanoTrabalhoSchema]: Esquema Pydantic do Plano
            de Trabalho encontrado ou None.
    """
    async with db_session as session:
        result = await session.execute(
            select(models.PlanoTrabalho)
            .filter_by(cod_SIAPE_instituidora=cod_SIAPE_instituidora)
            .filter_by(id_plano_trabalho_participante=id_plano_trabalho_participante)
        )
        db_plano_trabalho = result.unique().scalar_one_or_none()
    if db_plano_trabalho:
        return schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho)
    return None


async def check_planos_trabalho_per_period(
    db_session: DbContextManager,
    cod_SIAPE_instituidora: int,
    cod_SIAPE_unidade_exercicio: int,
    cpf_participante: str,
    id_plano_trabalho_participante: int,
    data_inicio_plano: date,
    data_termino_plano: date,
) -> bool:
    """Verifica se há outros Planos de Trabalho no período informado,
    para a mesma unidade instituidora, mesma unidade de exercício e mesmo
    participante, gerando um conflito de sobreposição de datas entre os
    planos de trabalho.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        cod_SIAPE_instituidora (int): Código SIAPE da unidade instituidora.
        cod_SIAPE_unidade_exercicio (int): Código SIAPE da unidade de
            exercício do participante.
        cpf_participante (str): CPF do participante.
        id_plano_trabalho_participante (int): id do Plano de Trabalho do
            participante.
        data_inicio_plano (date): Data de início do Plano de Trabalho.
        data_termino_plano (date): Data de término do Plano de Trabalho.

    Returns:
        bool: True se há conflito; False caso contrário.
    """
    async with db_session as session:
        query = (
            select(func.count())
            .select_from(models.PlanoTrabalho)
            .filter_by(cod_SIAPE_instituidora=cod_SIAPE_instituidora)
            .filter_by(cod_SIAPE_unidade_exercicio=cod_SIAPE_unidade_exercicio)
            .filter_by(cpf_participante=cpf_participante)
            .filter_by(cancelado=False)
            .where(
                and_(
                    (
                        # exclui o próprio plano de trabalho da verificação para
                        # não conflitar com ele mesmo
                        models.PlanoTrabalho.id_plano_trabalho_participante
                        != id_plano_trabalho_participante
                    ),
                    (models.PlanoTrabalho.data_inicio_plano <= data_termino_plano),
                    (models.PlanoTrabalho.data_termino_plano >= data_inicio_plano),
                )
            )
        )
        result = await session.execute(query)
        count_plano_trabalho = result.scalar()
    if count_plano_trabalho > 0:
        return True
    return False


async def create_plano_trabalho(
    db_session: DbContextManager,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
) -> schemas.PlanoTrabalhoSchema:
    """Cria um plano de trabalho definido pelos dados do schema Pydantic
    plano_trabalho.

    Args:
        db_session (DbContextManager): Context manager para a sessão
            async do SQL Alchemy.
        plano_trabalho (schemas.PlanoTrabalhoSchema): Dados do plano
            de trabalho como um esquema Pydantic.

    Returns:
        schemas.PlanoEntregasSchema: Esquema Pydantic do Plano de Trabalho
            com os dados que foram gravados no banco.
    """
    creation_timestamp = datetime.now()
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
    db_plano_trabalho.data_insercao = creation_timestamp
    async with db_session as session:
        for contribuicao in contribuicoes:
            contribuicao.data_insercao = creation_timestamp
            contribuicao.id_plano_entrega_unidade = (
                plano_trabalho.id_plano_entrega_unidade
            )
            session.add(contribuicao)
            db_plano_trabalho.contribuicoes.append(contribuicao)
            db_plano_trabalho.contribuicoes = contribuicoes
        for consolidacao in consolidacoes:
            consolidacao.data_insercao = creation_timestamp
            session.add(consolidacao)
            db_plano_trabalho.consolidacoes.append(consolidacao)
        session.add(db_plano_trabalho)
        try:
            await session.commit()
        except IntegrityError as e:
            raise HTTPException(
                status_code=422, detail="Referência a tabela entrega não encontrada"
            ) from e
        await session.refresh(db_plano_trabalho)
    return schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho)


async def update_plano_trabalho(
    db_session: DbContextManager,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
) -> schemas.PlanoTrabalhoSchema:
    """Atualiza um plano de trabalho conforme os dados recebidos no
    esquema Pydantic em plano_trabalho.

    Os dados existentes são primeiro apagados do banco para depois
    inserir os dados recebidos.

    Args:
        db_session (DbContextManager): Context manager para a sessão
            async do SQL Alchemy.
        plano_trabalho (schemas.PlanoTrabalhoSchema): Dados do plano
            de trabalho como um esquema Pydantic.

    Returns:
        schemas.PlanoEntregasSchema: Esquema Pydantic do Plano de Trabalho
            com o retorno de create_plano_trabalho.
    """
    async with db_session as session:
        result = await session.execute(
            select(models.PlanoTrabalho)
            .filter_by(cod_SIAPE_instituidora=plano_trabalho.cod_SIAPE_instituidora)
            .filter_by(
                id_plano_trabalho_participante=plano_trabalho.id_plano_trabalho_participante
            )
        )
        db_plano_trabalho = result.unique().scalar_one()
        await session.delete(db_plano_trabalho)
        await session.commit()
    return await create_plano_trabalho(db_session, plano_trabalho)


async def get_plano_entregas(
    db_session: DbContextManager,
    cod_SIAPE_instituidora: int,
    id_plano_entrega_unidade: int,
) -> Optional[schemas.PlanoEntregasSchema]:
    """Traz um plano de entregas a partir do banco de dados, consultando
    a partir dos parâmetros informados.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        cod_SIAPE_instituidora (int): Código SIAPE da unidade instituidora.
        id_plano_entrega_unidade (int): id do Plano de Entregas da Unidade.

    Returns:
        Optional[schemas.PlanoEntregasSchema]: O Plano de Entregas
            encontrado ou None.
    """
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


async def check_planos_entregas_unidade_per_period(
    db_session: DbContextManager,
    cod_SIAPE_instituidora: int,
    cod_SIAPE_unidade_plano: int,
    id_plano_entrega_unidade: int,
    data_inicio_plano_entregas: date,
    data_termino_plano_entregas: date,
) -> bool:
    """Verifica se há outros Planos de Entrega no período informado,
    para a mesma unidade instituidora e mesma unidade do plano, gerando
    um conflito de sobreposição de datas entre os planos de entregas.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        cod_SIAPE_instituidora (int): Código SIAPE da unidade instituidora.
        cod_SIAPE_unidade_plano (int): Código SIAPE da unidade do Plano
            de Entregas.
        id_plano_entrega_unidade (int): id do Plano de Entregas da unidade.
        data_inicio_plano_entregas (date): Data de início do Plano de
            Entregas.
        data_termino_plano_entregas (date): Data de término do Plano de
            Entregas.

    Returns:
        bool: True se há conflito; False caso contrário.
    """
    async with db_session as session:
        query = (
            select(func.count())
            .select_from(models.PlanoEntregas)
            .filter_by(cod_SIAPE_instituidora=cod_SIAPE_instituidora)
            .filter_by(cod_SIAPE_unidade_plano=cod_SIAPE_unidade_plano)
            .filter_by(cancelado=False)
            .where(
                and_(
                    (
                        # exclui o próprio plano de entregas da verificação
                        # para não conflitar com ele mesmo
                        models.PlanoEntregas.id_plano_entrega_unidade
                        != id_plano_entrega_unidade
                    ),
                    (
                        models.PlanoEntregas.data_inicio_plano_entregas
                        <= data_termino_plano_entregas
                    ),
                    (
                        models.PlanoEntregas.data_termino_plano_entregas
                        >= data_inicio_plano_entregas
                    ),
                )
            )
        )
        result = await session.execute(query)
        count_plano_entregas = result.scalar()
    if count_plano_entregas > 0:
        return True
    return False


async def create_plano_entregas(
    db_session: DbContextManager,
    plano_entregas: schemas.PlanoEntregasSchema,
) -> schemas.PlanoEntregasSchema:
    """Cria um plano de trabalho definido pelos dados do schema Pydantic
    plano_entregas.

    Args:
        db_session (DbContextManager): Context manager para a sessão
            async do SQL Alchemy.
        plano_entregas (schemas.PlanoEntregasSchema): Dados do plano
            de entregas como um esquema Pydantic.

    Returns:
        schemas.PlanoEntregasSchema: Esquema Pydantic do Plano de Entregas
            com os dados que foram gravados no banco.
    """
    creation_timestamp = datetime.now()
    entregas = [
        models.Entrega(**entrega.model_dump()) for entrega in plano_entregas.entregas
    ]
    plano_entregas.entregas = []
    db_plano_entregas = models.PlanoEntregas(**plano_entregas.model_dump())
    db_plano_entregas.data_insercao = creation_timestamp
    async with db_session as session:
        for entrega in entregas:
            entrega.data_insercao = creation_timestamp
            session.add(entrega)
            db_plano_entregas.entregas.append(entrega)
            db_plano_entregas.entregas = entregas
        session.add(db_plano_entregas)
        await session.commit()
        await session.refresh(db_plano_entregas)
    return schemas.PlanoEntregasSchema.model_validate(db_plano_entregas)


async def update_plano_entregas(
    db_session: DbContextManager,
    plano_entregas: schemas.PlanoEntregasSchema,
) -> schemas.PlanoEntregasSchema:
    """Atualiza um plano de entregas conforme os dados recebidos no
    esquema Pydantic em plano_entregas.

    Os dados existentes são primeiro apagados do banco para depois
    inserir os dados recebidos.

    Args:
        db_session (DbContextManager): Context manager para a sessão
            async do SQL Alchemy.
        plano_entregas (schemas.PlanoEntregasSchema): Dados do plano
            de entregas como um esquema Pydantic.

    Returns:
        schemas.PlanoEntregasSchema: Esquema Pydantic do Plano de Entregas
            com o retorno de create_plano_entregas.
    """
    async with db_session as session:
        result = await session.execute(
            select(models.PlanoEntregas)
            .filter_by(cod_SIAPE_instituidora=plano_entregas.cod_SIAPE_instituidora)
            .filter_by(id_plano_entrega_unidade=plano_entregas.id_plano_entrega_unidade)
        )
        db_plano_entregas = result.unique().scalar_one()
        await session.delete(db_plano_entregas)
        await session.commit()
    return await create_plano_entregas(db_session, plano_entregas)


async def get_participante(
    db_session: DbContextManager,
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    cpf: str,
) -> Optional[schemas.ParticipanteSchema]:
    """Traz os status do participante a partir do banco de dados, consultando
    a partir dos parâmetros informados.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        cod_unidade_autorizadora (int): Código SIAPE da unidade instituidora.
        cpf (str): CPF do participante.

    Returns:
        Optional[schemas.tatusParticipanteSchema]: Lista de Status
            de Participante, cada item contendo um esquema Pydantic
            representando um Status de participante. Ou None se não houver.
    """
    async with db_session as session:
        result = await session.execute(
            select(models.Participante)
            .filter_by(origem_unidade=origem_unidade)
            .filter_by(cod_unidade_autorizadora=cod_unidade_autorizadora)
            .filter_by(cpf=cpf)
        )
        db_list_status_participante = result.scalars().all()
    if db_list_status_participante:
        return {
            "lista_status": [
                schemas.ParticipanteSchema.model_validate(status_participante)
                for status_participante in db_list_status_participante
            ]
        }
    return None


async def create_participante(
    db_session: DbContextManager,
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    status_participante: schemas.ParticipanteSchema,
) -> schemas.ParticipanteSchema:
    """Cria um status de participante definido pelos dados do schema Pydantic
    status_participante.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        status_participante (schemas.ParticipanteSchema): Esquema
            do Pydantic de um Status de Participante.

    Returns:
        schemas.ParticipanteSchema: Esquema do Pydantic de um Status
        de Participante dos dados inseridos.
    """

    db_status_participante = models.StatusParticipante(
        **status_participante.model_dump()
    )
    db_status_participante.data_insercao = datetime.now()
    async with db_session as session:
        session.add(db_status_participante)
        await session.commit()
        await session.refresh(db_status_participante)
    return schemas.ParticipanteSchema.model_validate(db_status_participante)


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


def truncate_participante():
    """Apaga a tabela status_participante.
    Usado no ambiente de testes de integração contínua.
    """
    with SyncSession.begin() as session:
        result = session.execute(text("TRUNCATE participante CASCADE;"))
    return result

def truncate_user():
    """Apaga a tabela users.
    Usado no ambiente de testes de integração contínua.
    """
    with SyncSession.begin() as session:
        result = session.execute(text("TRUNCATE users CASCADE;"))
    return result
