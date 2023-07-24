from datetime import timedelta
import json
import logging

from pydantic import ValidationError
from starlette.responses import JSONResponse
from fastapi import Depends, FastAPI, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi_mail import FastMail, MessageSchema
from pydantic import BaseModel, EmailStr

import models, schemas, crud, util
from database import engine, get_db
from auth import user_db, User, UserCreate, UserUpdate, UserDB, SECRET_KEY
from auth import database_meta as auth_db
from email_conf import conf

ACCESS_TOKEN_EXPIRE_MINUTES = 30

models.Base.metadata.create_all(bind=engine)

with open('docs/description.md', 'r') as f:
    description = f.read()

app = FastAPI(
    title="Plataforma de recebimento de dados do Programa de Gestão - PGD",
    description=description,
    version="0.1.8",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/jwt/login")

async def send_email(user: List[str],
                     subject: str,
                     body: str) -> JSONResponse:
    """Envia e-mail para um destinatário."""

    message = MessageSchema(
        subject=subject,
        recipients=user,
        html=body,
        subtype="html"
        )
    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "Email enviado!"})


async def on_after_register(user: UserDB, request: Request):
    logging.info("User %s has registered.", user.id)

async def on_after_forgot_password(user: UserDB, token: str, request: Request):
    logging.info("User %s has forgot their password. Reset token: %s",
                    user.id, token)
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

async def on_after_reset_password(user: UserDB, request: Request):
    logging.info("User %s has reset their password.", user.id)
    subject = "Alteração de senha"
    body = f"""
            <html>
            <body>
            <h3>Alteração de senha</h3>
            <p>Olá, {user.email}.</p>
            <p>Sua senha da API PGD foi alterada.
            Se não reconhecer esta alteração, verifique seu acesso.
            </p>
            </body>
            </html>
            """
    await send_email([user.email], subject, body)

bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET_KEY, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers(
    user_db,
    [auth_backend],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
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
        SECRET_KEY, after_forgot_password=on_after_forgot_password, after_reset_password=on_after_reset_password
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

@app.get("/", include_in_schema=False)
async def docs_redirect(
    accept: Union[str, None] = Header(default='text/html')):
    """
    Redireciona para a documentação da API.
    """
    if accept == "application/json":
        location = "/openapi.json"
    else:
        location = "/docs"
    return RedirectResponse(url=location,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@app.put("/plano_trabalho/{cod_plano}",
        summary="Cria ou substitui plano de trabalho",
        response_model=schemas.PlanoTrabalhoSchema
        )
async def create_or_update_plano_trabalho(
    cod_plano: str,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    user: User = Depends(fastapi_users.current_user(active=True))
    ):
    """Cria um novo plano de trabalho ou, se existente, substitui um
    plano de trabalho por um novo com os dados informados."""
    # Validações da entrada conforme regras de negócio
    if cod_plano != plano_trabalho.cod_plano:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro cod_plano diferente do conteúdo do JSON")

    db_plano_trabalho = crud.get_plano_trabalho(db, user.cod_unidade,
                                                    cod_plano)
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
            crud.update_plano_trabalho(db, plano_trabalho,
                                                user.cod_unidade)
        else:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Usuário não pode alterar Plano de Trabalho"+
                        " de outra unidade.")
    return plano_trabalho

@app.patch("/plano_trabalho/{cod_plano}",
        summary="Atualiza plano de trabalho",
        response_model=schemas.PlanoTrabalhoSchema
        )
async def patch_plano_trabalho(
    cod_plano: str,
    plano_trabalho: schemas.PlanoTrabalhoUpdateSchema,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    user: User = Depends(fastapi_users.current_user(active=True))
    ):
    "Atualiza um plano de trabalho existente nos campos informados."
    # Validações da entrada conforme regras de negócio
    if cod_plano != plano_trabalho.cod_plano:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro cod_plano diferente do conteúdo do JSON")

    db_plano_trabalho = crud.get_plano_trabalho(db, user.cod_unidade,
                                                        cod_plano)
    if db_plano_trabalho is None:
        raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Só é possível aplicar PATCH em um recurso"+
                        " existente.")
    if db_plano_trabalho.cod_unidade != user.cod_unidade:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Usuário não pode alterar Plano de Trabalho"+
                    " de outra unidade.")

    # atualiza os atributos, exceto atividades
    merged_plano_trabalho = util.sa_obj_to_dict(db_plano_trabalho)
    patch_plano_trabalho = plano_trabalho.dict(exclude_unset=True)
    if patch_plano_trabalho.get("atividades", None):
        del patch_plano_trabalho["atividades"]
    merged_plano_trabalho.update(patch_plano_trabalho)

    # atualiza as atividades

    # traz a lista de atividades que está no banco
    db_atividades = util.list_to_dict(
        [
            util.sa_obj_to_dict(atividade)
            for atividade in getattr(db_plano_trabalho, "atividades", list())
        ],
        "id_atividade"
    )

    # cada atividade a ser modificada
    patch_atividades = util.list_to_dict(
        plano_trabalho.dict(exclude_unset=True).get("atividades", list()),
        "id_atividade"
    )

    merged_atividades = util.merge_dicts(db_atividades, patch_atividades)
    merged_plano_trabalho["atividades"] = util.dict_to_list(
        merged_atividades,
        "id_atividade"
    )

    # tenta validar o esquema

    # para validar o esquema, é necessário ter o atributo atividades,
    # mesmo que seja uma lista vazia
    if merged_plano_trabalho.get("atividades", None) is None:
        merged_plano_trabalho["atividades"] = []
    # valida o esquema do plano de trabalho atualizado
    try:
        merged_schema = schemas.PlanoTrabalhoSchema(**merged_plano_trabalho)
    except ValidationError as e:
        raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=json.loads(e.json())
    )

    crud.update_plano_trabalho(db, merged_schema, user.cod_unidade)
    return merged_plano_trabalho

@app.get("/plano_trabalho/{cod_plano}",
        summary="Consulta plano de trabalho",
        response_model=schemas.PlanoTrabalhoSchema
        )
async def get_plano_trabalho(cod_plano: str,
                       db: Session = Depends(get_db),
                       token: str = Depends(oauth2_scheme),
                       user: User = Depends(fastapi_users.current_user(active=True))
                       ):
    "Consulta o plano de trabalho com o código especificado."
    db_plano_trabalho = crud.get_plano_trabalho(db, user.cod_unidade, cod_plano)
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
    paths = openapi_schema["paths"]
    del paths["/truncate_pts_atividades"]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = public_facing_openapi
