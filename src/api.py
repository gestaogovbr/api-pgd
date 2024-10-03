"""Definição das rotas, endpoints e seu comportamento na API.
"""

from datetime import timedelta
import json
import os
from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, status, Header, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError


import crud
import crud_auth
from db_config import DbContextManager, create_db_and_tables
import email_config
import response_schemas
import schemas
from util import check_permissions

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))
TEST_ENVIRONMENT = os.environ.get("TEST_ENVIRONMENT", "False") == "True"

# ## INIT --------------------------------------------------

with open(
    os.path.join(os.path.dirname(__file__), "docs", "description.md"),
    "r",
    encoding="utf-8",
) as f:
    description = f.read()

if TEST_ENVIRONMENT:
    with open(
        os.path.join(os.path.dirname(__file__), "docs", "environment.md"),
        "r",
        encoding="utf-8",
    ) as f:
        environment_msg = f.read()

    description = environment_msg + description

app = FastAPI(
    title="Plataforma de recebimento de dados do Programa de Gestão - PGD",
    description=description,
    version=os.getenv("TAG_NAME", "dev-build") or "dev-build",
)


@app.on_event("startup")
async def on_startup():
    """Executa as rotinas de inicialização da API."""
    await create_db_and_tables()
    await crud_auth.init_user_admin()


@app.middleware("http")
async def check_user_agent(request: Request, call_next):
    user_agent = request.headers.get("User-Agent", None)

    if not user_agent:
        return JSONResponse(
            status_code=400,
            content={"detail": "User-Agent header is required"},
        )
    return await call_next(request)


@app.get("/", include_in_schema=False)
async def docs_redirect(
    accept: Union[str, None] = Header(default="text/html")
) -> RedirectResponse:
    """
    Redireciona para a documentação da API.
    """

    if accept == "application/json":
        location = "/openapi.json"
    else:
        location = "/docs"

    return RedirectResponse(
        url=location, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )


# ## AUTH --------------------------------------------------


@app.post(
    "/token",
    summary="Autentica na API.",
    tags=["Auth"],
    response_model=schemas.Token,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": response_schemas.ValidationErrorResponse,
            "description": response_schemas.ValidationErrorResponse.get_title(),
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid email format": {
                            "value": response_schemas.ValidationErrorResponse(
                                detail=[
                                    response_schemas.ValidationError(
                                        type="value_error",
                                        loc=["email"],
                                        msg="value is not a valid email address: "
                                        "An email address must have an @-sign.",
                                        input="my_username",
                                        ctx={
                                            "reason": "An email address must have an @-sign."
                                        },
                                        url="https://errors.pydantic.dev/2.8/v/value_error",
                                    )
                                ]
                            ).json()
                        }
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": response_schemas.UnauthorizedErrorResponse,
            "description": response_schemas.UnauthorizedErrorResponse.get_title(),
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid credentials": {
                            "value": {"detail": "Username ou password incorretos"}
                        }
                    }
                }
            },
        },
    },
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbContextManager = Depends(DbContextManager),
) -> dict:
    """Realiza o login na API usando as credenciais de acesso, obtendo um
    token de acesso."""
    try:
        schemas.UsersInputSchema(email=form_data.username)
    except Exception as exception:
        message = getattr(exception, "message", str(exception))
        if getattr(exception, "json", None):
            message = exception.json()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
        ) from exception

    user = await crud_auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ou password incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud_auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get(
    "/users",
    summary="Lista usuários da API.",
    tags=["Auth"],
    response_model=list[schemas.UsersGetSchema],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized access",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid credentials": {
                            "value": {"detail": "Not authenticated"}
                        }
                    }
                }
            },
        },
    },
)
async def get_users(
    user_logged: Annotated[  # pylint: disable=unused-argument
        schemas.UsersSchema,
        Depends(crud_auth.get_current_admin_user),
    ],
    db: DbContextManager = Depends(DbContextManager),
) -> list[schemas.UsersGetSchema]:
    """Obtém a lista de usuários da API."""
    return await crud_auth.get_all_users(db)


@app.put(
    "/user/{email}",
    summary="Cria ou altera usuário na API.",
    tags=["Auth"],
)
async def create_or_update_user(
    user_logged: Annotated[  # pylint: disable=unused-argument
        schemas.UsersSchema, Depends(crud_auth.get_current_admin_user)
    ],
    user: schemas.UsersSchema,
    email: str,
    db: DbContextManager = Depends(DbContextManager),
) -> JSONResponse:
    """Cria um usuário da API ou atualiza os seus dados cadastrais."""

    # Validações

    # ## url
    if email != user.email:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email deve ser igual na url e no json",
        )

    # ## schema
    try:
        schemas.UsersSchema.model_validate(user)
    except Exception as exception:
        message = getattr(exception, "message", str(exception))
        if getattr(exception, "json", None):
            message = json.loads(getattr(exception, "json"))
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
        ) from exception

    # Call
    response_status = status.HTTP_200_OK
    try:
        # update
        if await crud_auth.get_user(db, user.email):
            await crud_auth.update_user(db, user)
        # create
        else:
            await crud_auth.create_user(db, user)
            response_status = status.HTTP_201_CREATED
    except IntegrityError as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IntegrityError: {str(exception)}",
        ) from exception

    return JSONResponse(
        content=user.dict(exclude=["password"]), status_code=response_status
    )


@app.get(
    "/user/{email}",
    summary="Consulta um usuário da API.",
    tags=["Auth"],
)
async def get_user(
    user_logged: Annotated[  # pylint: disable=unused-argument
        schemas.UsersSchema,
        Depends(crud_auth.get_current_admin_user),
    ],
    email: str,
    db: DbContextManager = Depends(DbContextManager),
) -> schemas.UsersGetSchema:
    """Retorna os dados cadastrais do usuário da API especificado pelo
    e-mail informado."""

    user = await crud_auth.get_user(db, email)

    if user:
        return user.dict(exclude=["password"])
    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Usuário `{email}` não existe"
        )


@app.post(
    "/user/forgot_password/{email}",
    summary="Solicita recuperação de acesso à API.",
    tags=["Auth"],
)
async def forgot_password(
    email: str,
    db: DbContextManager = Depends(DbContextManager),
) -> schemas.UsersInputSchema:
    """Dispara o processo de recuperação de senha, enviando um token de
    redefinição de senha ao e-mail informado no cadastro do usuário."""

    user = await crud_auth.get_user(db, email)

    if user:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = crud_auth.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        return await email_config.send_reset_password_mail(email, access_token)

    raise HTTPException(
        status.HTTP_404_NOT_FOUND, detail=f"Usuário `{email}` não existe"
    )


@app.get(
    "/user/reset_password/",
    summary="Criar nova senha a partir do token de acesso.",
    tags=["Auth"],
)
async def reset_password(
    access_token: str,
    password: str,
    db: DbContextManager = Depends(DbContextManager),
):
    """
    Gera uma nova senha através do token fornecido por email.
    """
    try:
        return await crud_auth.user_reset_password(db, access_token, password)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e}") from e


# ## DATA --------------------------------------------------


# ### Entregas & Plano Entregas ----------------------------
@app.get(
    "/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
    "/plano_entregas/{id_plano_entregas}",
    summary="Consulta plano de entregas",
    response_model=schemas.PlanoEntregasSchema,
    tags=["plano de entregas"],
)
async def get_plano_entrega(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    id_plano_entregas: str,
    db: DbContextManager = Depends(DbContextManager),
):
    "Consulta o plano de entregas com o código especificado."

    # Validações de permissão
    check_permissions(origem_unidade, cod_unidade_autorizadora, user)

    db_plano_entrega = await crud.get_plano_entregas(
        db_session=db,
        origem_unidade=origem_unidade,
        cod_unidade_autorizadora=cod_unidade_autorizadora,
        id_plano_entregas=id_plano_entregas,
    )
    if not db_plano_entrega:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Plano de entregas não encontrado"
        )
    # plano_trabalho = schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho.__dict__)
    return db_plano_entrega.__dict__


@app.put(
    "/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
    "/plano_entregas/{id_plano_entregas}",
    summary="Cria ou substitui plano de entregas",
    response_model=schemas.PlanoEntregasSchema,
    tags=["plano de entregas"],
)
async def create_or_update_plano_entregas(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    id_plano_entregas: str,
    plano_entregas: schemas.PlanoEntregasSchema,
    response: Response,
    db: DbContextManager = Depends(DbContextManager),
):
    """Cria um novo plano de entregas ou, se existente, substitui um
    plano de entregas por um novo com os dados informados."""

    # Validações de permissão
    check_permissions(origem_unidade, cod_unidade_autorizadora, user)

    # Validações de conteúdo JSON e URL
    for field in ("origem_unidade", "cod_unidade_autorizadora", "id_plano_entregas"):
        if locals().get(field) != getattr(plano_entregas, field):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Parâmetro {field} na URL e no JSON devem ser iguais",
            )

    # Validações do esquema
    try:
        novo_plano_entregas = schemas.PlanoEntregasSchema.model_validate(plano_entregas)
    except Exception as exception:
        message = getattr(exception, "message", str(exception))
        if getattr(exception, "json", None):
            message = json.loads(getattr(exception, "json"))
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
        ) from exception

    # Verifica se há sobreposição da data de inicio e fim do plano
    # com planos já existentes
    conflicting_period = await crud.check_planos_entregas_unidade_per_period(
        db_session=db,
        origem_unidade=origem_unidade,
        cod_unidade_autorizadora=cod_unidade_autorizadora,
        cod_unidade_executora=plano_entregas.cod_unidade_executora,
        id_plano_entregas=plano_entregas.id_plano_entregas,
        data_inicio=plano_entregas.data_inicio,
        data_termino=plano_entregas.data_termino,
    )

    if conflicting_period and plano_entregas.status != 1:
        detail_msg = (
            "Já existe um plano de entregas para este "
            "cod_unidade_executora no período informado."
        )
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail_msg)

    # Verifica se já existe
    db_plano_entregas = await crud.get_plano_entregas(
        db_session=db,
        origem_unidade=origem_unidade,
        cod_unidade_autorizadora=cod_unidade_autorizadora,
        id_plano_entregas=id_plano_entregas,
    )

    try:
        if not db_plano_entregas:  # create
            novo_plano_entregas = await crud.create_plano_entregas(
                db_session=db,
                plano_entregas=novo_plano_entregas,
            )
            response.status_code = status.HTTP_201_CREATED
        else:  # update
            novo_plano_entregas = await crud.update_plano_entregas(
                db_session=db,
                plano_entregas=novo_plano_entregas,
            )
        return novo_plano_entregas
    except IntegrityError as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IntegrityError: {str(exception)}",
        ) from exception


# ### Plano Trabalho ---------------------------------------
@app.get(
    "/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
    "/plano_trabalho/{id_plano_trabalho}",
    summary="Consulta plano de trabalho",
    response_model=schemas.PlanoTrabalhoSchema,
    tags=["plano de trabalho"],
)
async def get_plano_trabalho(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    id_plano_trabalho: str,
    db: DbContextManager = Depends(DbContextManager),
):
    "Consulta o plano de trabalho com o código especificado."

    # Validações de permissão
    check_permissions(origem_unidade, cod_unidade_autorizadora, user)

    db_plano_trabalho = await crud.get_plano_trabalho(
        db_session=db,
        origem_unidade=origem_unidade,
        cod_unidade_autorizadora=cod_unidade_autorizadora,
        id_plano_trabalho=id_plano_trabalho,
    )
    if not db_plano_trabalho:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Plano de trabalho não encontrado"
        )
    # plano_trabalho = schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho.__dict__)
    return db_plano_trabalho.__dict__


@app.put(
    "/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
    "/plano_trabalho/{id_plano_trabalho}",
    summary="Cria ou substitui plano de trabalho",
    response_model=schemas.PlanoTrabalhoSchema,
    tags=["plano de trabalho"],
)
async def create_or_update_plano_trabalho(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    id_plano_trabalho: str,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
    response: Response,
    db: DbContextManager = Depends(DbContextManager),
):
    """Cria um novo plano de trabalho ou, se existente, substitui um
    plano de trabalho por um novo com os dados informados."""

    # Validações de permissão
    check_permissions(origem_unidade, cod_unidade_autorizadora, user)

    # Validações de conteúdo JSON e URL
    for field in ("origem_unidade", "cod_unidade_autorizadora", "id_plano_trabalho"):
        if locals().get(field) != getattr(plano_trabalho, field):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Parâmetro {field} na URL e no JSON devem ser iguais",
            )

    # Validações do esquema
    try:
        novo_plano_trabalho = schemas.PlanoTrabalhoSchema.model_validate(plano_trabalho)
    except Exception as exception:
        message = getattr(exception, "message", str(exception))
        if getattr(exception, "json", None):
            message = json.loads(getattr(exception, "json"))
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
        ) from exception

    # Verifica se há sobreposição da data de inicio e fim do plano
    # com planos já existentes
    conflicting_period = await crud.check_planos_trabalho_per_period(
        db_session=db,
        origem_unidade=origem_unidade,
        cod_unidade_autorizadora=cod_unidade_autorizadora,
        cod_unidade_executora=plano_trabalho.cod_unidade_executora,
        matricula_siape=plano_trabalho.matricula_siape,
        id_plano_trabalho=plano_trabalho.id_plano_trabalho,
        data_inicio=plano_trabalho.data_inicio,
        data_termino=plano_trabalho.data_termino,
    )

    if plano_trabalho.status != 1 and conflicting_period:
        detail_msg = (
            "Já existe um plano de trabalho para este "
            "cod_SIAPE_unidade_exercicio para esta matrícula "
            "no período informado."
        )
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail_msg)

    # Verifica se já existe
    db_plano_trabalho = await crud.get_plano_trabalho(
        db_session=db,
        origem_unidade=origem_unidade,
        cod_unidade_autorizadora=cod_unidade_autorizadora,
        id_plano_trabalho=id_plano_trabalho,
    )

    try:
        if not db_plano_trabalho:  # create
            novo_plano_trabalho = await crud.create_plano_trabalho(
                db_session=db,
                plano_trabalho=novo_plano_trabalho,
            )
            response.status_code = status.HTTP_201_CREATED
        else:  # update
            novo_plano_trabalho = await crud.update_plano_trabalho(
                db_session=db,
                plano_trabalho=novo_plano_trabalho,
            )
            response.status_code = status.HTTP_200_OK
    except IntegrityError as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IntegrityError: {str(exception)}",
        ) from exception
    except ValueError as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exception),
        ) from exception

    return novo_plano_trabalho


# ### Participante ---------------------------------------
@app.get(
    "/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
    "/{cod_unidade_lotacao}/participante/{matricula_siape}",
    summary="Consulta um Participante",
    response_model=schemas.ParticipanteSchema,
    tags=["participante"],
)
async def get_participante(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    cod_unidade_lotacao: int,
    matricula_siape: str,
    db: DbContextManager = Depends(DbContextManager),
) -> schemas.ParticipanteSchema:
    "Consulta o participante a partir da matricula SIAPE."

    #  Validações de permissão
    check_permissions(origem_unidade, cod_unidade_autorizadora, user)

    participante = await crud.get_participante(
        db_session=db,
        origem_unidade=origem_unidade,
        cod_unidade_autorizadora=cod_unidade_autorizadora,
        cod_unidade_lotacao=cod_unidade_lotacao,
        matricula_siape=matricula_siape,
    )
    if not participante:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Participante não encontrado"
        )

    return participante


@app.put(
    "/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
    "/{cod_unidade_lotacao}/participante/{matricula_siape}",
    summary="Envia um participante",
    response_model=schemas.ParticipanteSchema,
    tags=["participante"],
)
async def create_or_update_participante(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    origem_unidade: str,
    cod_unidade_autorizadora: int,
    cod_unidade_lotacao: int,
    matricula_siape: str,
    participante: schemas.ParticipanteSchema,
    response: Response,
    db: DbContextManager = Depends(DbContextManager),
) -> schemas.ParticipanteSchema:
    """Envia um ou mais status de Programa de Gestão de um participante."""

    # Validações de permissão
    check_permissions(origem_unidade, cod_unidade_autorizadora, user)

    # Validações de conteúdo JSON e URL
    for field in (
        "origem_unidade",
        "cod_unidade_autorizadora",
        "cod_unidade_lotacao",
        "matricula_siape",
    ):
        if locals().get(field) != getattr(participante, field):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Parâmetro {field} na URL e no JSON devem ser iguais",
            )

    # Validações do esquema
    try:
        novo_participante = schemas.ParticipanteSchema.model_validate(participante)
    except Exception as exception:
        message = getattr(exception, "message", str(exception))
        if getattr(exception, "json", None):
            message = json.loads(getattr(exception, "json"))
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
        ) from exception

    # Verifica se já existe
    db_participante = await crud.get_participante(
        db_session=db,
        origem_unidade=origem_unidade,
        cod_unidade_autorizadora=cod_unidade_autorizadora,
        cod_unidade_lotacao=cod_unidade_lotacao,
        matricula_siape=matricula_siape,
    )

    # Gravar no banco de dados
    try:
        if not db_participante:  # create
            novo_participante = await crud.create_participante(
                db_session=db,
                participante=novo_participante,
            )
            response.status_code = status.HTTP_201_CREATED
        else:  # update
            novo_participante = await crud.update_participante(
                db_session=db,
                participante=novo_participante,
            )
    except IntegrityError as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IntegrityError: {str(exception)}",
        ) from exception

    # retornar os dados gravados como Pydantic
    participante_gravado = schemas.ParticipanteSchema.model_validate(novo_participante)

    return participante_gravado
