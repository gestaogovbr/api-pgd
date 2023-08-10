import os
from typing import AsyncGenerator, List

from fastapi.security import OAuth2AuthorizationCodeBearer
from starlette.responses import JSONResponse
from fief_client import FiefAsync
from fief_client.integrations.fastapi import FiefAuth
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = "HS256"
SQLALCHEMY_DATABASE_URL = os.environ["SQLALCHEMY_DATABASE_URL"]
FIEF_BASE_TENANT_URL = os.environ["FIEF_BASE_TENANT_URL"]
FIEF_CLIENT_ID = os.environ["FIEF_CLIENT_ID"]
FIEF_CLIENT_SECRET = os.environ["FIEF_CLIENT_SECRET"]

fief = FiefAsync(
    base_url=FIEF_BASE_TENANT_URL,
    client_id=FIEF_CLIENT_ID,
    client_secret=FIEF_CLIENT_SECRET,
)

scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{FIEF_BASE_TENANT_URL}/authorize",
    tokenUrl=f"{FIEF_BASE_TENANT_URL}/api/token",
    scopes={"openid": "openid"},
    auto_error=False,
)

auth_backend = FiefAuth(fief, scheme)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# database models (SQLAlchemy)
class Base(DeclarativeBase):
    pass

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


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

