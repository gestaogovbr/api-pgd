from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import List, Optional
from pydantic import BaseModel
from fastapi_users import models as user_models
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
import databases
import sqlalchemy
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy import event, DDL
from database import SessionLocal, engine, SQLALCHEMY_DATABASE_URL


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

class User(user_models.BaseUser):
    cod_unidade: int

class UserCreate(user_models.BaseUserCreate):
    cod_unidade: int

class UserUpdate(User, user_models.BaseUserUpdate):
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
                detail=f"Não tem permissão para alterar o atributo.")
        return d

class UserDB(User, user_models.BaseUserDB):
    pass

database_meta = databases.Database(SQLALCHEMY_DATABASE_URL)

Base: DeclarativeMeta = declarative_base()

class UserTable(Base, SQLAlchemyBaseUserTable):
    cod_unidade = Column(BigInteger)
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime)
    pass

users = UserTable.__table__

trigger = DDL("""
    CREATE TRIGGER inseredata_trigger
    BEFORE INSERT OR UPDATE ON public.user
    FOR EACH ROW EXECUTE PROCEDURE insere_data_registro();
"""
)

event.listen(
    UserTable.__table__,
    'after_create',
    trigger.execute_if(dialect='postgresql')
)

user_db = SQLAlchemyUserDatabase(UserDB, database_meta, users)

engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL)

Base.metadata.create_all(engine)

class UserInDB(User):
    hashed_password: str

