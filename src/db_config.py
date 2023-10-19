"""Funções para estabelecer conexões com o banco de dados e sessões.
"""

import os
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

SQLALCHEMY_DATABASE_URL = os.environ["SQLALCHEMY_DATABASE_URL"]

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
sync_engine = create_engine(SQLALCHEMY_DATABASE_URL)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
SyncSession = sessionmaker(sync_engine)


# database models (SQLAlchemy)
class Base(DeclarativeBase):
    pass


async def create_db_and_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # remover depois
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_db():
    db = get_async_session()
    try:
        yield db
    finally:
        db.aclose()

class DbContextManager:
    def __init__(self):
        self.db = async_session_maker()

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.db.close()
