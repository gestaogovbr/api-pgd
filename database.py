from typing import AsyncGenerator
import os

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event, DDL
from sqlalchemy import Table

SQLALCHEMY_DATABASE_URL = os.environ['SQLALCHEMY_DATABASE_URL']

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

Base = declarative_base()

func = DDL("""
    CREATE OR REPLACE FUNCTION insere_data_registro()
    RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                new.data_insercao = current_timestamp;
                RETURN NEW;    
            ELSEIF (TG_OP = 'UPDATE') THEN
                new.data_atualizacao = current_timestamp;
                RETURN NEW;
            END IF;
        END;
    $$ LANGUAGE PLPGSQL
"""
)

event.listen(
    Table,
    'after_create',
    func.execute_if(dialect='postgresql')
)


def get_db():
    db = get_async_session()
    try:
        yield db
    finally:
        db.close()

