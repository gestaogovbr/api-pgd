"""Funções para ler, gravar, atualizar ou apagar dados no banco de dados.
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, and_, func
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

import models, schemas
from db_config import DbContextManager, sync_engine


async def get_plano_trabalho(
    db_session: DbContextManager,
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    id_plano_trabalho: str,
) -> Optional[schemas.PlanoTrabalhoSchema]:
    """Traz um plano de trabalho a partir do banco de dados, consultando
    a partir dos parâmetros informados.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        origem_unidade (str): Código do sistema da unidade: “SIAPE” ou “SIORG”
        cod_unidade_autorizadora (int): Código da unidade autorizadora.
        id_plano_trabalho (str): id do Plano de Trabalho
    Returns:
        Optional[schemas.PlanoTrabalhoSchema]: Esquema Pydantic do Plano
            de Trabalho encontrado ou None.
    """
    async with db_session as session:
        result = await session.execute(
            select(models.PlanoTrabalho)
            .filter_by(origem_unidade=origem_unidade)
            .filter_by(cod_unidade_autorizadora=cod_unidade_autorizadora)
            .filter_by(id_plano_trabalho=id_plano_trabalho)
        )
        db_plano_trabalho = result.unique().scalar_one_or_none()
    if db_plano_trabalho:
        return schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho)
    return None


async def check_planos_trabalho_per_period(
    db_session: DbContextManager,
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    cod_unidade_executora: int,
    matricula_siape: str,
    id_plano_trabalho: int,
    data_inicio: date,
    data_termino: date,
) -> bool:
    """Verifica se há outros Planos de Trabalho no período informado,
    para a mesma unidade instituidora, mesma unidade de exercício e mesmo
    participante, gerando um conflito de sobreposição de datas entre os
    planos de trabalho.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        origem_unidade (str): Código do sistema da unidade: “SIAPE” ou “SIORG”
        cod_unidade_autorizadora (int): Código da unidade autorizadora.
        cod_unidade_executora (int): Código da unidade executora.
        matricula_siape (str): Matrícula siape do participante.
        id_plano_trabalho (int): id do Plano de Trabalho.
        data_inicio (date): Data de início do Plano de Trabalho.
        data_termino (date): Data de término do Plano de Trabalho.

    Returns:
        bool: True se há conflito; False caso contrário.
    """
    async with db_session as session:
        query = (
            select(func.count())
            .select_from(models.PlanoTrabalho)
            .filter_by(origem_unidade=origem_unidade)
            .filter_by(cod_unidade_autorizadora=cod_unidade_autorizadora)
            .filter_by(cod_unidade_executora=cod_unidade_executora)
            .filter_by(matricula_siape=matricula_siape)
            .filter(models.PlanoTrabalho.status != 1)
            .where(
                and_(
                    (
                        # exclui o próprio plano de trabalho da verificação para
                        # não conflitar com ele mesmo
                        models.PlanoTrabalho.id_plano_trabalho
                        != id_plano_trabalho
                    ),
                    (models.PlanoTrabalho.data_inicio <= data_termino),
                    (models.PlanoTrabalho.data_termino >= data_inicio),
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
        schemas.PlanoTrabalhoSchema: Esquema Pydantic do Plano de Trabalho
            com os dados que foram gravados no banco.
    """
    creation_timestamp = datetime.now()
    contribuicoes = (
        [
            models.Contribuicao(
                origem_unidade_pt=plano_trabalho.origem_unidade,
                cod_unidade_autorizadora_pt=plano_trabalho.cod_unidade_autorizadora,
                id_plano_trabalho=plano_trabalho.id_plano_trabalho,
                **contribuicao.model_dump(),
            )
            for contribuicao in plano_trabalho.contribuicoes
        ]
        if plano_trabalho.contribuicoes
        else []
    )

    avaliacoes_registros_execucao = [
        models.AvaliacaoRegistrosExecucao(**avaliacao_registros_execucao.model_dump())
        for avaliacao_registros_execucao in plano_trabalho.avaliacoes_registros_execucao
    ]
    # Esvazia as listas para poder converter o plano_trabalho para SQL Alchemy
    plano_trabalho.contribuicoes = []
    plano_trabalho.avaliacoes_registros_execucao = []
    db_plano_trabalho = models.PlanoTrabalho(**plano_trabalho.model_dump())
    db_plano_trabalho.data_insercao = creation_timestamp
    async with db_session as session:
        # Estabelece relacionamentos
        # Relacionamento com Participante
        query = (
            select(models.Participante)
            .filter_by(origem_unidade=plano_trabalho.origem_unidade)
            .filter_by(cod_unidade_autorizadora=plano_trabalho.cod_unidade_autorizadora)
            .filter_by(matricula_siape=plano_trabalho.matricula_siape)
            .filter_by(
                cod_unidade_lotacao=plano_trabalho.cod_unidade_lotacao_participante
            )
        )
        result = await session.execute(query)
        db_participante = result.scalars().unique().one_or_none()
        if db_participante is None:
            raise ValueError(
                "Plano de Trabalho faz referência a participante inexistente. "
                f"origem_unidade: {plano_trabalho.origem_unidade} "
                f"cod_unidade_autorizadora: {plano_trabalho.cod_unidade_autorizadora} "
                f"matricula_siape: {plano_trabalho.matricula_siape} "
                f"cod_unidade_lotacao: {plano_trabalho.cod_unidade_lotacao_participante}"
            )
        db_plano_trabalho.participante = db_participante

        # Relacionamento com Contribuicao
        for contribuicao in contribuicoes:
            contribuicao.data_insercao = creation_timestamp
            # Relacionamento com Entrega, se existir
            contribuicao.entrega = None
            if (
                contribuicao.tipo_contribuicao == 1
                and contribuicao.id_plano_entregas
                and contribuicao.id_entrega
            ):
                query = (
                    select(models.Entrega)
                    .filter_by(origem_unidade=plano_trabalho.origem_unidade)
                    .filter_by(
                        cod_unidade_autorizadora=plano_trabalho.cod_unidade_autorizadora
                    )
                    .filter_by(id_plano_entregas=contribuicao.id_plano_entregas)
                    .filter_by(id_entrega=contribuicao.id_entrega)
                )
                result = await session.execute(query)
                db_entrega = result.scalars().unique().one_or_none()
                if db_entrega is None:
                    raise ValueError(
                        "Contribuição do Plano de Trabalho faz referência a entrega "
                        "inexistente. "
                        f"origem_unidade: {plano_trabalho.origem_unidade} "
                        "cod_unidade_autorizadora: "
                        f"{plano_trabalho.cod_unidade_autorizadora} "
                        f"id_plano_entregas: {contribuicao.id_plano_entregas} "
                        f"id_entrega: {contribuicao.id_entrega}"
                    )
                contribuicao.entrega = db_entrega
        db_plano_trabalho.contribuicoes = contribuicoes

        # Relacionamento com AvaliacaoRegistrosExecucao
        for avaliacao_registros_execucao in avaliacoes_registros_execucao:
            avaliacao_registros_execucao.data_insercao = creation_timestamp
        db_plano_trabalho.avaliacoes_registros_execucao = avaliacoes_registros_execucao
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
        schemas.PlanoTrabalhoSchema: Esquema Pydantic do Plano de Trabalho
            com o retorno de create_plano_trabalho.
    """
    async with db_session as session:
        result = await session.execute(
            select(models.PlanoTrabalho)
            .filter_by(origem_unidade=plano_trabalho.origem_unidade)
            .filter_by(cod_unidade_autorizadora=plano_trabalho.cod_unidade_autorizadora)
            .filter_by(id_plano_trabalho=plano_trabalho.id_plano_trabalho)
        )
        db_plano_trabalho = result.unique().scalar_one()
        await session.delete(db_plano_trabalho)
        await session.commit()
    return await create_plano_trabalho(db_session, plano_trabalho)


async def get_plano_entregas(
    db_session: DbContextManager,
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    id_plano_entregas: int,
) -> Optional[schemas.PlanoEntregasSchema]:
    """Traz um plano de entregas a partir do banco de dados, consultando
    a partir dos parâmetros informados.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        origem_unidade (str): origem do código da unidade (SIAPE ou SIORG).
        cod_unidade_autorizadora (int): Código SIAPE da unidade instituidora.
        id_plano_entregas (int): id do Plano de Entregas da Unidade.

    Returns:
        Optional[schemas.PlanoEntregasSchema]: O Plano de Entregas
            encontrado ou None.
    """
    async with db_session as session:
        result = await session.execute(
            select(models.PlanoEntregas)
            .filter_by(origem_unidade=origem_unidade)
            .filter_by(cod_unidade_autorizadora=cod_unidade_autorizadora)
            .filter_by(id_plano_entregas=id_plano_entregas)
        )
        db_plano_entrega = result.unique().scalar_one_or_none()
    if db_plano_entrega:
        return db_plano_entrega
    return None


async def check_planos_entregas_unidade_per_period(
    db_session: DbContextManager,
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    cod_unidade_executora: int,
    id_plano_entregas: int,
    data_inicio: date,
    data_termino: date,
) -> bool:
    """Verifica se há outros Planos de Entrega no período informado,
    para a mesma unidade instituidora e mesma unidade do plano, gerando
    um conflito de sobreposição de datas entre os planos de entregas.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        origem_unidade (str): Origem do código da unidade.
        cod_unidade_autorizadora (int): Código da unidade autorizadora.
        cod_unidade_executora (int): Código da unidade do Plano
            de Entregas.
        id_plano_entregas (int): id do Plano de Entregas da unidade.
        data_inicio (date): Data de início do Plano de Entregas.
        data_termino (date): Data de término do Plano de Entregas.

    Returns:
        bool: True se há conflito; False caso contrário.
    """
    async with db_session as session:
        query = (
            select(func.count())
            .select_from(models.PlanoEntregas)
            .filter_by(origem_unidade=origem_unidade)
            .filter_by(cod_unidade_autorizadora=cod_unidade_autorizadora)
            .filter_by(cod_unidade_executora=cod_unidade_executora)
            .filter(models.PlanoEntregas.status != 1)
            .filter(
                and_(
                    (
                        # exclui o próprio plano de entregas da verificação
                        # para não conflitar com ele mesmo
                        models.PlanoEntregas.id_plano_entregas
                        != id_plano_entregas
                    ),
                    (models.PlanoEntregas.data_inicio <= data_termino),
                    (models.PlanoEntregas.data_termino >= data_inicio),
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
            .filter_by(origem_unidade=plano_entregas.origem_unidade)
            .filter_by(cod_unidade_autorizadora=plano_entregas.cod_unidade_autorizadora)
            .filter_by(id_plano_entregas=plano_entregas.id_plano_entregas)
        )
        db_plano_entregas = result.unique().scalar_one()
        await session.delete(db_plano_entregas)
        await session.commit()
    return await create_plano_entregas(db_session, plano_entregas)


async def get_participante(
    db_session: DbContextManager,
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    cod_unidade_lotacao: int,
    matricula_siape: str,
) -> Optional[schemas.ParticipanteSchema]:
    """Traz o participante a partir do banco de dados, consultando a
    partir dos parâmetros informados.

    Args:
        db_session (DbContextManager): Context manager para a sessão
            async do SQL Alchemy.
        origem_unidade (str): Origem do sistema da unidade: "SIAPE" ou
            "SIORG"
        cod_unidade_autorizadora (int): Código da unidade autorizadora.
        cod_unidade_lotacao (int): Código da unidade de lotação.
        matricula_siape (Optional[str]): Matrícula SIAPE do participante.
            If omitted, will return the first one found.

    Returns:
        Optional[schemas.ParticipanteSchema]: Participante, contendo um
            esquema Pydantic representando um participante. Ou None se
            não houver.
    """
    async with db_session as session:
        query = (
            select(models.Participante)
            .filter_by(origem_unidade=origem_unidade)
            .filter_by(cod_unidade_autorizadora=cod_unidade_autorizadora)
            .filter_by(cod_unidade_lotacao=cod_unidade_lotacao)
            .filter_by(matricula_siape=matricula_siape)
        )
        result = await session.execute(query)
        db_participante = result.scalars().unique().one_or_none()
    if db_participante:
        return schemas.ParticipanteSchema.model_validate(db_participante)
    return None


async def create_participante(
    db_session: DbContextManager,
    participante: schemas.ParticipanteSchema,
) -> schemas.ParticipanteSchema:
    """Cria um participante definido pelos dados do schema Pydantic
    participante.

    Args:
        db_session (DbContextManager): Context manager para a sessão async
            do SQL Alchemy.
        participante (schemas.ParticipanteSchema): Esquema
            do Pydantic de um Participante.

    Returns:
        schemas.ParticipanteSchema: Esquema do Pydantic de um Status
        de Participante dos dados inseridos.
    """

    async with db_session as session:
        db_participante = models.Participante(**participante.model_dump())
        db_participante.data_insercao = datetime.now()
        session.add(db_participante)
        await session.commit()
        await session.refresh(db_participante)
    return schemas.ParticipanteSchema.model_validate(db_participante)


async def update_participante(
    db_session: DbContextManager,
    participante: schemas.ParticipanteSchema,
) -> schemas.ParticipanteSchema:
    """Atualiza um participante conforme os dados recebidos no
    esquema Pydantic em participante.

    Os dados existentes são primeiro apagados do banco para depois
    inserir os dados recebidos.

    Args:
        db_session (DbContextManager): Context manager para a sessão
            async do SQL Alchemy.
        participante (schemas.ParticipanteSchema): Dados do plano
            de entregas como um esquema Pydantic.

    Returns:
        schemas.ParticipanteSchema: Esquema Pydantic do Participante
            com o retorno de create_participante.
    """
    async with db_session as session:
        # find and delete
        result = await session.execute(
            select(models.Participante)
            .filter_by(origem_unidade=participante.origem_unidade)
            .filter_by(cod_unidade_autorizadora=participante.cod_unidade_autorizadora)
            .filter_by(cod_unidade_lotacao=participante.cod_unidade_lotacao)
            .filter_by(matricula_siape=participante.matricula_siape)
        )
        db_participante = result.unique().scalar_one()
        for field, value in participante.model_dump().items():
            setattr(db_participante, field, value)
        db_participante.data_atualizacao = datetime.now()
        await session.commit()
        await session.refresh(db_participante)
    return schemas.ParticipanteSchema.model_validate(db_participante)


# The following methods are only for test in CI/CD environment


def truncate_plano_entregas():
    """Apaga a tabela plano_entregas.
    Usado no ambiente de testes de integração contínua.
    """
    with sync_engine.connect() as conn:
        result = conn.execute(text("TRUNCATE plano_entregas, entrega CASCADE;"))
        conn.commit()
    return result


def truncate_plano_trabalho():
    """Apaga a tabela plano_trabalho.
    Usado no ambiente de testes de integração contínua.
    """
    with sync_engine.connect() as conn:
        result = conn.execute(
            text(
                "TRUNCATE avaliacao_registros_execucao, contribuicao, "
                "plano_trabalho CASCADE;"
            )
        )
        conn.commit()
    return result


def truncate_participante():
    """Apaga a tabela status_participante.
    Usado no ambiente de testes de integração contínua.
    """
    with sync_engine.connect() as conn:
        result = conn.execute(text("TRUNCATE participante CASCADE;"))
        result2 = conn.execute(text("SELECT 1;"))
        result2.one_or_none()
        conn.commit()
    return result


def truncate_user():
    """Apaga a tabela users.
    Usado no ambiente de testes de integração contínua.
    """
    with sync_engine.connect() as conn:
        result = conn.execute(text("TRUNCATE users CASCADE;"))
        conn.commit()
    return result
