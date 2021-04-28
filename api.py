from datetime import timedelta
import json

from pydantic import ValidationError
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi.openapi.utils import get_openapi

import models, schemas, crud
from database import engine, get_db
from auth import user_db, User, UserCreate, UserUpdate, UserDB, SECRET_KEY
from auth import database_meta as auth_db

ACCESS_TOKEN_EXPIRE_MINUTES = 30

models.Base.metadata.create_all(bind=engine)

description = """
O **Programa de Gestão** é a política da Administração Pública Federal para ...

Esta API permite que órgãos federais submetam os Planos de Trabalhos da sua força de trabalho para a SEGES/ME.

Para solicitar credenciais para submissão de dados, entre em contato com [email-de-apoio@economia.gov.br](mailto:email-do-suporte@economia.gov.br)

-------

Os **Planos de Trabalhos** submetidos devem seguir as seguintes regras:
* O `cod_plano` deve ser único para cada Plano de Trabalho.
* Ao utilizar o método PUT do Plano de Trabalho, o `cod_plano` que compõe a URL deve ser igual ao fornecido no JSON.
* A `data_inicio` do Plano de Trabalho deve ser menor ou igual à `data_fim`.
* A `data_avaliacao` da atividade deve ser maior ou igual que a `data_fim` do Plano de Trabalho.
* As atividades de um mesmo Plano de Trabalho devem possuir `id_atividade` diferentes.
* O `cpf` deve possuir exatamente 11 dígitos e sem máscaras.
* Valores permitidos para a `modalidade_execucao`:
  * **1** - Presencial
  * **2** - Semipresencial
  * **3** - Teletrabalho
* `carga_horaria_semanal` deve ser entre 1 e 40.
* A soma dos tempos `tempo_exec_presencial` e `tempo_exec_teletrabalho` das atividades deve ser igual à `carga_horaria_total` do Plano de Trabalho.
* Os campos `quantidade_entregas`, `quantidade_entregas_efetivas`, `tempo_exec_presencial`, `tempo_exec_teletrabalho` da Atividade e `horas_homologadas` do Plano de Trabalho devem ser maiores que zero.* `entregue_no_prazo` não é obrigatório e deve ser `True` ou `False` caso esteja preenchido.
* Explore a seção [**Schemas**](#model-AtividadeSchema) nesta documentação para descobrir quais campos são obrigatórios para as Atividades e os Planos de Trabalho.

"""

app = FastAPI(
    title="Plataforma do Programa de Gestão - PGD",
    description=description,
    version="0.1.0",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/jwt/login")

async def on_after_register(user: UserDB, request: Request):
    print(f"User {user.id} has registered.")


async def on_after_forgot_password(user: UserDB, token: str, request: Request):
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
    tags=["auth"],
    dependencies=[Depends(fastapi_users.current_user(active=True, superuser=True))]
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
    plano_trabalho: schemas.PlanoTrabalhoUpdateSchema,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    user: User = Depends(fastapi_users.current_user(active=True))
    ):
    # Validações da entrada conforme regras de negócio
    if cod_plano != plano_trabalho.cod_plano:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro cod_plano diferente do conteúdo do JSON")

    db_plano_trabalho = crud.get_plano_trabalho(db, cod_plano)
    if db_plano_trabalho is None: # create
        try:
            novo_plano_trabalho = schemas.PlanoTrabalhoSchema(
                                                **plano_trabalho.dict())
            crud.create_plano_tabalho(db, novo_plano_trabalho,
                                                    user.cod_unidade)
        except ValidationError as e:
            raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=json.loads(e.json())
        )
    else: # update
        if db_plano_trabalho.cod_unidade == user.cod_unidade:
            try:
                merged_plano_trabalho = {
                    k: v
                    for k, v in db_plano_trabalho.__dict__.items()
                    if k[0] != '_'
                }
                merged_plano_trabalho.update(
                    plano_trabalho.dict(exclude_unset=True))
                schemas.PlanoTrabalhoSchema(**merged_plano_trabalho)
            except ValidationError as e:
                raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=json.loads(e.json())
            )
            crud.update_plano_tabalho(db, plano_trabalho)
            return merged_plano_trabalho
        else:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Usuário não pode alterar Plano de Trabalho"+
                        " de outra unidade.")
    return plano_trabalho

@app.get("/plano_trabalho/{cod_plano}",
         response_model=schemas.PlanoTrabalhoSchema
        )
async def get_plano_trabalho(cod_plano: str,
                       db: Session = Depends(get_db),
                       token: str = Depends(oauth2_scheme),
                    #    user: User = Depends(fastapi_users.current_user())
                       ):
    db_plano_trabalho = crud.get_plano_trabalho(db, cod_plano)
    if db_plano_trabalho is None:
        raise HTTPException(404, detail="Plano de trabalho não encontrado")
    plano_trabalho = schemas.PlanoTrabalhoSchema.from_orm(db_plano_trabalho)
    return plano_trabalho.__dict__

@app.post("/truncate_pts_atividades")
async def truncate_pts_atividades(
        db: Session = Depends(get_db),
        user: User = Depends(fastapi_users.current_user(
            active=True,
            superuser=True
        ))):
    crud.truncate_pts_atividades(db)


# Esconde alguns métodos da interface OpenAPI

def public_facing_openapi():
    " Cria o esquema da OpenAPI disponível ao público externo."
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title = app.title,
        description = app.description,
        version = app.version,
        routes = app.routes
    )
    paths = openapi_schema['paths']
    del paths['/truncate_pts_atividades']
    del paths['/users/{id}']
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = public_facing_openapi
