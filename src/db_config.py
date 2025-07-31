"""Funções para estabelecer conexões com o banco de dados e sessões.
"""

import os
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import text
from db_audit import AUDIT_DDL

SQLALCHEMY_DATABASE_URL = os.environ["SQLALCHEMY_DATABASE_URL"]

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
sync_engine = create_engine(SQLALCHEMY_DATABASE_URL)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


# database models (SQLAlchemy)
class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Classe base para modelos SQL Alchemy.
    """


async def create_db_and_tables():
    """"Inicializa o banco de dados e as tabelas, se não existirem.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_audit_ddl():

    async with engine.begin() as conn:
        await conn.execute(text(AUDIT_DDL))


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Retorna a sessão do banco de dados.

    Returns:
        AsyncGenerator[AsyncSession, None]: gerador assíncrono para
            sessões do banco de dados.

    Yields:
        Iterator[AsyncGenerator[AsyncSession, None]]: iterador para
            receber uma sessão.
    """
    async with async_session_maker() as session:
        yield session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Retorna sessões do banco de dados.

    Returns:
    AsyncGenerator[AsyncSession, None]: gerador assíncrono para
        sessões do banco de dados.

    Yields:
        Iterator[AsyncGenerator[AsyncSession, None]]: iterador para
        receber uma sessão.
    """
    async for db in get_async_session():
        yield db


async def check_db_connection(db: AsyncSession):
    """Verifica a conectividade com o banco de dados usando uma query
    leve.
    """
    result = await db.execute(text("SELECT 1"))
    _ = result.scalar_one_or_none()


class DbContextManager:
    """Context manager para manipulação de sessões do banco de dados.
    """
    def __init__(self):
        self.db = async_session_maker()

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.db.close()
