import os
from datetime import datetime
import uuid
from typing import AsyncGenerator, Optional, List
import logging

from fastapi import Depends, Request, HTTPException, status
from starlette.responses import JSONResponse
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users import schemas as user_schemas
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import Column, BigInteger
from pydantic import Field

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("FASTAPI_USERS_KEY")
ALGORITHM = "HS256"
SQLALCHEMY_DATABASE_URL = os.environ["SQLALCHEMY_DATABASE_URL"]

# Simulated users DB for tests
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


# database models (SQLAlchemy)
class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    cod_unidade: Mapped[int] = mapped_column(BigInteger())
    data_atualizacao: Mapped[datetime] = mapped_column()
    data_insercao: Mapped[datetime] = mapped_column()


# validation schemas (pydantic)
class UserRead(user_schemas.BaseUser[uuid.UUID]):
    cod_unidade: int = Field(
        title="código da unidade",
        description="código SIAPE da unidade de lotação do usuário da API",
    )
    data_atualizacao: datetime = Field(title="data e hora da última atualização")
    data_insercao: datetime = Field(title="data e hora de criação do registro")


class UserCreate(user_schemas.BaseUserCreate):
    """Schema model to create an API user."""

    cod_unidade: int

    def create_update_dict(self) -> dict:
        user_dict = super().create_update_dict()
        user_dict["data_insercao"] = user_dict[
            "data_atualizacao"
        ] = datetime.now().isoformat()


class UserUpdate(user_schemas.BaseUserUpdate):
    """Schema model to update an API user."""

    cod_unidade: int

    # O superusuário usa o método create_update_dict_superuser, então
    # não é afetado pelo código abaixo. Essa foi a solução encontrada
    # para proibir o usuário comum de alterar a propriedade.
    # Vide https://github.com/frankie567/fastapi-users/discussions/537
    def create_update_dict(self) -> dict:
        user_dict = super().create_update_dict()
        cod_unidade = user_dict.pop("cod_unidade", None)
        if cod_unidade is not None:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="Não tem permissão para alterar o atributo.",
            )
        user_dict["data_atualizacao"] = datetime.now().isoformat()
        return user_dict


class UserDB(UserRead, user_schemas.BaseUser):
    pass


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET_KEY, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # remover depois
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, UserRead)


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


class UserManager(UUIDIDMixin, BaseUserManager[UserRead, uuid.UUID]):
    reset_password_token_secret = SECRET_KEY
    verification_token_secret = SECRET_KEY

    async def on_after_register(
        self, user: UserRead, request: Optional[Request] = None
    ):
        logging.info("User %s has registered.", user.id)

    async def on_after_forgot_password(
        self, user: UserRead, token: str, request: Optional[Request] = None
    ):
        logging.info(
            "User %s has forgot their password. Reset token: %s", user.id, token
        )
        subject = "Recuperação de acesso"
        body = f"""
                <html>
                <body>
                <h3>Recuperação de acesso</h3>
                <p>Olá, {user.email}.</p>
                <p>Você esqueceu sua senha da API PGD.
                Segue seu novo token de acesso: <br/> {token}
                </p>
                </body>
                </html>
                """
        await send_email([user.email], subject, body)

    async def on_after_request_verify(
        self, user: UserRead, token: str, request: Optional[Request] = None
    ):
        logging.info(
            "Verification requested for user %s. Verification token: %s", user.id, token
        )


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


def get_db():
    db = get_async_session()
    try:
        yield db
    finally:
        db.aclose()


api_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
