from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

import models, schemas, crud
from database import engine, get_db
from auth import user_db, User, UserCreate, UserUpdate, UserDB, SECRET_KEY
from auth import database as auth_db

ACCESS_TOKEN_EXPIRE_MINUTES = 30

models.Base.metadata.create_all(bind=engine)

description = """
O **Programa de Gestão** é a política da Administração Pública Federal para ...

De acordo com a norma [IN nº65/2020](https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-65-de-30-de-julho-de-2020-269669395) todos os órgãos devem submeter ao órgão central todas
as informações sobre os Planos de Trabalho que estão sendo realizados naquela
instituição. A submissão deve ser realizada através desta **API**.
[melhorar estes textos!!]

Para solicitar credenciais para submissão de dados, entre em contato com [email-do-suporte@economia.gov.br](mailto:email-do-suporte@economia.gov.br)
"""

app = FastAPI(
    title="Plataforma do Programa de Gestão - PGD",
    description=description,
    version="0.1.0",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/jwt/login")

def on_after_register(user: UserDB, request: Request):
    print(f"User {user.id} has registered.")


def on_after_forgot_password(user: UserDB, token: str, request: Request):
    print(f"User {user.id} has forgot their password. Reset token: {token}")

jwt_authentication = JWTAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=3600,
    tokenUrl="/auth/jwt/login"
)

fastapi_users = FastAPIUsers(
    user_db,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

app.include_router(
    fastapi_users.get_auth_router(jwt_authentication),
    prefix="/auth/jwt",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(on_after_register),
    prefix="/auth",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_reset_password_router(
        SECRET_KEY, after_forgot_password=on_after_forgot_password
    ),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(),
    prefix="/users",
    tags=["users"]
)


@app.on_event("startup")
async def startup():
    await auth_db.connect()

@app.on_event("shutdown")
async def shutdown():
    await auth_db.disconnect()

@app.put("/plano_trabalho/{cod_plano}",
         response_model=schemas.PlanoTrabalhoSchema
         )
async def create_or_update_plano_trabalho(
    cod_plano: str,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
    db: Session = Depends(get_db),
    # token: str = Depends(oauth2_scheme)
    ):
    if cod_plano != plano_trabalho.cod_plano:
        return HTTPException(
            400,
            detail="Parâmetro cod_plano diferente do conteúdo do JSON")

    db_plano_trabalho = crud.get_plano_trabalho(db, cod_plano)

    if db_plano_trabalho is None:
        crud.create_plano_tabalho(db, plano_trabalho)
    else:
        crud.update_plano_tabalho(db, plano_trabalho)
    return plano_trabalho

@app.get("/plano_trabalho/{cod_plano}",
         response_model=schemas.PlanoTrabalhoSchema
        )
def get_plano_trabalho(cod_plano: str,
                       db: Session = Depends(get_db),
                    #    token: str = Depends(oauth2_scheme)
                       ):
    plano_trabalho = crud.get_plano_trabalho(db, cod_plano)
    if plano_trabalho is None:
        return HTTPException(404, detail="Plano de trabalho não encontrado")
    return plano_trabalho.__dict__