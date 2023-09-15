"""Funções para estabelecer conexões com o banco de dados e sessões.
"""

import os
from typing import AsyncGenerator, List

from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ALGORITHM = "HS256"
SQLALCHEMY_DATABASE_URL = os.environ["SQLALCHEMY_DATABASE_URL"]

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


# database models (SQLAlchemy)
class Base(DeclarativeBase):
    pass


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # remover depois
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def send_email(user: List[str], subject: str, body: str) -> JSONResponse:
    """Envia e-mail para um destinatário."""
    conf = ConnectionConfig(
        MAIL_USERNAME=os.environ["MAIL_USERNAME"],
        MAIL_FROM=os.environ["MAIL_FROM"],
        MAIL_PORT=os.environ["MAIL_PORT"],
        MAIL_SERVER=os.environ["MAIL_SERVER"],
        MAIL_FROM_NAME=os.environ["MAIL_FROM_NAME"],
        MAIL_TLS=False,
        MAIL_SSL=False,
        MAIL_PASSWORD=os.environ["MAIL_PASSWORD"],
        USE_CREDENTIALS=False,
        VALIDATE_CERTS=False,
    )
    message = MessageSchema(subject=subject, recipients=user, html=body, subtype="html")
    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "Email enviado!"})


async def get_db():
    db = get_async_session()
    try:
        yield db
    finally:
        db.aclose()
