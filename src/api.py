"""Definição das rotas, endpoints e seu comportamento na API.
"""

from datetime import timedelta
from typing import Annotated
import os
from typing import Union
import json

from fastapi import Depends, FastAPI, HTTPException, status, Header, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError


import schemas
import crud
from db_config import DbContextManager, create_db_and_tables
import crud_auth
from create_admin_user import init_user_admin
import email_config

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))


# ## INIT --------------------------------------------------


with open(
    os.path.join(os.path.dirname(__file__), "docs", "description.md"),
    "r",
    encoding="utf-8",
) as f:
    description = f.read()

app = FastAPI(
    title="Plataforma de recebimento de dados do Programa de Gestão - PGD",
    description=description,
    version=os.environ["TAG_NAME"],
)


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
    await init_user_admin()


@app.get("/", include_in_schema=False)
async def docs_redirect(accept: Union[str, None] = Header(default="text/html")):
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
    summary="Autentica na api-pgd",
    response_model=schemas.Token,
    tags=["Auth"],
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbContextManager = Depends(DbContextManager),
):
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
    summary="Consulta usuários da api-pgd",
    tags=["Auth"],
)
async def get_users(
    user_logged: Annotated[ # pylint: disable=unused-argument
        schemas.UsersSchema,
        Depends(crud_auth.get_current_admin_user),
    ],
    db: DbContextManager = Depends(DbContextManager),
) -> list[schemas.UsersGetSchema]:
    return await crud_auth.get_all_users(db)


@app.put(
    "/user/{email}",
    summary="Cria ou edita usuário na api-pgd",
    tags=["Auth"],
)
async def create_or_update_user(
    user_logged: Annotated[  # pylint: disable=unused-argument
        schemas.UsersSchema, Depends(crud_auth.get_current_admin_user)
    ],
    user: schemas.UsersSchema,
    email: str,
    db: DbContextManager = Depends(DbContextManager),
) -> dict:
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
    try:
        # update
        if await crud_auth.get_user(db, user.email):
            await crud_auth.update_user(db, user)
        # create
        else:
            await crud_auth.create_user(db, user)
    except IntegrityError as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IntegrityError: {str(exception)}",
        ) from exception

    return user.dict(exclude=["password"])


@app.get(
    "/user/{email}",
    summary="Consulta usuários da api-pgd",
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
    user = await crud_auth.get_user(db, email)

    if user:
        return user.dict(exclude=["password"])
    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Usuário `{email}` não existe"
        )


@app.delete(
    "/user/{email}",
    summary="Deleta usuário na api-pgd",
    tags=["Auth"],
)
async def delete_user(
    user_logged: Annotated[
        schemas.UsersInputSchema, Depends(crud_auth.get_current_admin_user)
    ],
    email: str,
    db: DbContextManager = Depends(DbContextManager),
):
    # Validações
    if user_logged.email == email:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não pode se auto deletar",
        )

    # Call
    try:
        return await crud_auth.delete_user(db, email)

    except IntegrityError as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IntegrityError: {str(exception)}",
        ) from exception


@app.post(
    "/user/forgot_password/{email}",
    summary="Recuperação de Acesso",
    tags=["Auth"],
)
async def forgot_password(
    email: str,
    db: DbContextManager = Depends(DbContextManager),
) -> schemas.UsersInputSchema:
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
    summary="Criar nova senha a partir do token de acesso",
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
    "/organizacao/{cod_SIAPE_instituidora}/plano_entregas/{id_plano_entrega_unidade}",
    summary="Consulta plano de entregas",
    response_model=schemas.PlanoEntregasSchema,
    tags=["plano de entregas"],
)
async def get_plano_entrega(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    id_plano_entrega_unidade: int,
    db: DbContextManager = Depends(DbContextManager),
):
    "Consulta o plano de entregas com o código especificado."
    db_plano_entrega = await crud.get_plano_entregas(
        db_session=db,
        cod_SIAPE_instituidora=user.cod_SIAPE_instituidora,
        id_plano_entrega_unidade=id_plano_entrega_unidade,
    )
    if not db_plano_entrega:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Plano de entregas não encontrado"
        )
    # plano_trabalho = schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho.__dict__)
    return db_plano_entrega.__dict__


@app.put(
    "/organizacao/{cod_SIAPE_instituidora}/plano_entregas/{id_plano_entrega_unidade}",
    summary="Cria ou substitui plano de entregas",
    response_model=schemas.PlanoEntregasSchema,
    tags=["plano de entregas"],
)
async def create_or_update_plano_entregas(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    cod_SIAPE_instituidora: int,
    id_plano_entrega_unidade: int,
    plano_entregas: schemas.PlanoEntregasSchema,
    response: Response,
    db: DbContextManager = Depends(DbContextManager),
    # TODO: Obter meios de verificar permissão opcional. O código abaixo
    #       bloqueia o acesso, mesmo informando que é opcional.
    # access_token_info: Optional[FiefAccessTokenInfo] = Depends(
    #     auth_backend.authenticated(permissions=["all:read"], optional=True)
    # ),
):
    """Cria um novo plano de entregas ou, se existente, substitui um
    plano de entregas por um novo com os dados informados."""

    # Validações de permissão
    if (
        cod_SIAPE_instituidora
        != user.cod_SIAPE_instituidora
        # TODO: Dar acesso ao superusuário em todas as unidades.
        # and "all:write" not in access_token_info["permissions"]
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não tem permissão na cod_SIAPE_instituidora informada",
        )

    # Validações de conteúdo JSON e URL
    if cod_SIAPE_instituidora != plano_entregas.cod_SIAPE_instituidora:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro cod_SIAPE_instituidora na URL e no JSON devem ser iguais",
        )
    if id_plano_entrega_unidade != plano_entregas.id_plano_entrega_unidade:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro cod_SIAPE_instituidora na URL e no JSON devem ser iguais",
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
        cod_SIAPE_instituidora=cod_SIAPE_instituidora,
        cod_SIAPE_unidade_plano=plano_entregas.cod_SIAPE_unidade_plano,
        id_plano_entrega_unidade=plano_entregas.id_plano_entrega_unidade,
        data_inicio_plano_entregas=plano_entregas.data_inicio_plano_entregas,
        data_termino_plano_entregas=plano_entregas.data_termino_plano_entregas,
    )

    if conflicting_period and not plano_entregas.cancelado:
        detail_msg = (
            "Já existe um plano de entregas para este "
            "cod_SIAPE_unidade_plano no período informado."
        )
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail_msg)

    # Verifica se já existe
    db_plano_entregas = await crud.get_plano_entregas(
        db_session=db,
        cod_SIAPE_instituidora=cod_SIAPE_instituidora,
        id_plano_entrega_unidade=id_plano_entrega_unidade,
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
    "/organizacao/{cod_SIAPE_instituidora}/plano_trabalho/{id_plano_trabalho_participante}",
    summary="Consulta plano de trabalho",
    response_model=schemas.PlanoTrabalhoSchema,
    tags=["plano de trabalho"],
)
async def get_plano_trabalho(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    id_plano_trabalho_participante: int,
    db: DbContextManager = Depends(DbContextManager),
):
    "Consulta o plano de trabalho com o código especificado."
    db_plano_trabalho = await crud.get_plano_trabalho(
        db_session=db,
        cod_SIAPE_instituidora=user.cod_SIAPE_instituidora,
        id_plano_trabalho_participante=id_plano_trabalho_participante,
    )
    if not db_plano_trabalho:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Plano de trabalho não encontrado"
        )
    # plano_trabalho = schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho.__dict__)
    return db_plano_trabalho.__dict__


@app.put(
    "/organizacao/{cod_SIAPE_instituidora}/plano_trabalho/{id_plano_trabalho_participante}",
    summary="Cria ou substitui plano de trabalho",
    response_model=schemas.PlanoTrabalhoSchema,
    tags=["plano de trabalho"],
)
async def create_or_update_plano_trabalho(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    cod_SIAPE_instituidora: int,
    id_plano_trabalho_participante: int,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
    response: Response,
    db: DbContextManager = Depends(DbContextManager),
    # TODO: Obter meios de verificar permissão opcional. O código abaixo
    #       bloqueia o acesso, mesmo informando que é opcional.
    # access_token_info: Optional[FiefAccessTokenInfo] = Depends(
    #     auth_backend.authenticated(permissions=["all:read"], optional=True)
    # ),
):
    """Cria um novo plano de trabalho ou, se existente, substitui um
    plano de trabalho por um novo com os dados informados."""

    # Validações de permissão
    if (
        cod_SIAPE_instituidora
        != user.cod_SIAPE_instituidora
        # TODO: Dar acesso ao superusuário em todas as unidades.
        # and "all:write" not in access_token_info["permissions"]
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não tem permissão na cod_SIAPE_instituidora informada",
        )

    # Validações de conteúdo JSON e URL
    if cod_SIAPE_instituidora != plano_trabalho.cod_SIAPE_instituidora:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro cod_SIAPE_instituidora diferente do conteúdo do JSON",
        )
    if id_plano_trabalho_participante != plano_trabalho.id_plano_trabalho_participante:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro id_plano_trabalho_participante na URL e no JSON devem ser iguais",
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
        cod_SIAPE_instituidora=cod_SIAPE_instituidora,
        cod_SIAPE_unidade_exercicio=plano_trabalho.cod_SIAPE_unidade_exercicio,
        cpf_participante=plano_trabalho.cpf_participante,
        id_plano_trabalho_participante=plano_trabalho.id_plano_trabalho_participante,
        data_inicio_plano=plano_trabalho.data_inicio_plano,
        data_termino_plano=plano_trabalho.data_termino_plano,
    )

    if conflicting_period and not plano_trabalho.cancelado:
        detail_msg = (
            "Já existe um plano de trabalho para este "
            "cod_SIAPE_unidade_exercicio para este cpf_participante "
            "no período informado."
        )
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail_msg)

    # Verifica se já existe
    db_plano_trabalho = await crud.get_plano_trabalho(
        db_session=db,
        cod_SIAPE_instituidora=cod_SIAPE_instituidora,
        id_plano_trabalho_participante=id_plano_trabalho_participante,
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
    except IntegrityError as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IntegrityError: {str(exception)}",
        ) from exception

    return novo_plano_trabalho


# ### Participante ---------------------------------------
@app.get(
    "/organizacao/{cod_SIAPE_instituidora}/participante/{cpf_participante}",
    summary="Consulta Status do Participante",
    response_model=schemas.ListaStatusParticipanteSchema,
    tags=["status participante"],
)
async def get_status_participante(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    cod_SIAPE_instituidora: int,
    cpf_participante: str,
    db: DbContextManager = Depends(DbContextManager),
) -> schemas.ListaStatusParticipanteSchema:
    "Consulta o status do participante a partir da matricula SIAPE."

    #  Validações de permissão
    if (
        cod_SIAPE_instituidora
        != user.cod_SIAPE_instituidora
        # TODO: Dar acesso ao superusuário em todas as unidades.
        # and "all:write" not in access_token_info["permissions"]
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não tem permissão na cod_SIAPE_instituidora informada",
        )

    lista_status_participante = await crud.get_status_participante(
        db_session=db,
        cod_SIAPE_instituidora=cod_SIAPE_instituidora,
        cpf_participante=cpf_participante,
    )
    if not lista_status_participante:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Status de Participante não encontrado"
        )

    return lista_status_participante


@app.put(
    "/organizacao/{cod_SIAPE_instituidora}/participante/{cpf_participante}",
    summary="Envia o status de um participante",
    response_model=schemas.ListaStatusParticipanteSchema,
    tags=["status participante"],
)
async def create_status_participante(
    user: Annotated[schemas.UsersSchema, Depends(crud_auth.get_current_active_user)],
    cod_SIAPE_instituidora: int,
    cpf_participante: str,
    lista_status_participante: schemas.ListaStatusParticipanteSchema,
    response: Response,
    db: DbContextManager = Depends(DbContextManager),
) -> schemas.ListaStatusParticipanteSchema:
    """Envia um ou mais status de Programa de Gestão de um participante."""

    # Validações de permissão
    if (
        cod_SIAPE_instituidora
        != user.cod_SIAPE_instituidora
        # TODO: Dar acesso ao superusuário em todas as unidades.
        # and "all:write" not in access_token_info["permissions"]
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não tem permissão na cod_SIAPE_instituidora informada",
        )
    for status_participante in lista_status_participante.lista_status:
        if cod_SIAPE_instituidora != status_participante.cod_SIAPE_instituidora:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Parâmetro cod_SIAPE_instituidora na URL e no JSON devem ser iguais",
            )
        if cpf_participante != status_participante.cpf_participante:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Parâmetro cpf_participante na URL e no JSON devem ser iguais",
            )

    # Validações do esquema
    try:
        nova_lista_status_participante = (
            schemas.ListaStatusParticipanteSchema.model_validate(
                lista_status_participante
            )
        )
    except Exception as exception:
        message = getattr(exception, "message", str(exception))
        if getattr(exception, "json", None):
            message = json.loads(getattr(exception, "json"))
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
        ) from exception

    # Gravar no banco de dados e retornar os dados gravados como Pydantic
    lista_gravada = schemas.ListaStatusParticipanteSchema.model_validate(
        {
            "lista_status": [
                await crud.create_status_participante(
                    db_session=db,
                    status_participante=status_participante,
                )
                for status_participante in nova_lista_status_participante.lista_status
            ]
        }
    )

    response.status_code = status.HTTP_201_CREATED
    return lista_gravada
