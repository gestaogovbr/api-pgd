import os
from datetime import timedelta
import uuid

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import List, Optional
from pydantic import BaseModel
from fastapi_users import schemas
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy import event, DDL

from database import engine, SQLALCHEMY_DATABASE_URL, get_user_db


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("FASTAPI_USERS_KEY")
ALGORITHM = "HS256"

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


class User(schemas.BaseUser):
    cod_unidade: int


class UserCreate(schemas.BaseUserCreate):
    cod_unidade: int


class UserUpdate(User, schemas.BaseUserUpdate):
    cod_unidade: int

    # O superusuário usa o método create_update_dict_superuser, então
    # não é afetado pelo código abaixo. Essa foi a solução encontrada
    # para proibir o usuário comum de alterar a propriedade.
    # Vide https://github.com/frankie567/fastapi-users/discussions/537
    def create_update_dict(self) -> dict:
        d = super().create_update_dict()
        p = d.pop("cod_unidade", None)
        if p is not None:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail=f"Não tem permissão para alterar o atributo.",
            )
        return d

class UserDB(User, schemas.BaseUser):
    pass

class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    # cod_unidade = Column(BigInteger)
    # data_atualizacao = Column(DateTime)
    # data_insercao = Column(DateTime)
    pass


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


trigger = DDL(
    """
    CREATE TRIGGER inseredata_trigger
    BEFORE INSERT OR UPDATE ON public.user
    FOR EACH ROW EXECUTE PROCEDURE insere_data_registro();
"""
)

event.listen(
    User.__table__, "after_create", trigger.execute_if(dialect="postgresql")
)

user_db = SQLAlchemyUserDatabase(User, )
