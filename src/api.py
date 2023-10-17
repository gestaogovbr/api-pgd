"""Definição das rotas, endpoints e seu comportamento na API.
"""

import os
from typing import Union, Optional
import json

from fastapi import Depends, FastAPI, HTTPException, status, Header
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fief_client import FiefUserInfo, FiefAccessTokenInfo
from sqlalchemy.orm import Session
import schemas
import crud
from db_config import get_db, create_db_and_tables
from users import auth_backend

with open("../docs/description.md", "r", encoding="utf-8") as f:
    description = f.read()

app = FastAPI(
    title="Plataforma de recebimento de dados do Programa de Gestão - PGD",
    description=description,
    version="0.2.0",
    swagger_ui_init_oauth={
        "clientId": os.environ["FIEF_CLIENT_ID"],
        "clientSecret": os.environ["FIEF_CLIENT_SECRET"],
        "scopes": "openid",
    },
)


@app.get("/user", summary="Consulta usuário da API", tags=["api"])
async def get_user(
    user: FiefUserInfo = Depends(auth_backend.current_user()),
):
    """Informações sobre o usuário autenticado na API."""
    return user


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


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


@app.get(
    "/organizacao/{cod_SIAPE_instituidora}/plano_trabalho/{id_plano_trabalho_participante}",
    summary="Consulta plano de trabalho",
    response_model=schemas.PlanoTrabalhoSchema,
    tags=["plano de trabalho"],
)
async def get_plano_trabalho(
    id_plano_trabalho_participante: int,
    db: Session = Depends(get_db),
    user: FiefUserInfo = Depends(auth_backend.current_user()),
):
    "Consulta o plano de trabalho com o código especificado."
    db_plano_trabalho = await crud.get_plano_trabalho(
        db_session=db,
        cod_SIAPE_instituidora=user["fields"]["cod_SIAPE_instituidora"],
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
    cod_SIAPE_instituidora: int,
    id_plano_trabalho_participante: int,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
    db: Session = Depends(get_db),
    user: FiefUserInfo = Depends(auth_backend.current_user()),
    access_token_info: Optional[FiefAccessTokenInfo] = Depends(
        auth_backend.authenticated(permissions=["all:read"])
    ),
):
    """Cria um novo plano de trabalho ou, se existente, substitui um
    plano de trabalho por um novo com os dados informados."""

    # Validações de permissão
    if (
        cod_SIAPE_instituidora != user["fields"]["cod_SIAPE_instituidora"]
        and "all:write" not in access_token_info["permissions"]
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Usuário não tem permissão na cod_SIAPE_instituidora informada",
        )
    if cod_SIAPE_instituidora != plano_trabalho.cod_SIAPE_instituidora:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro cod_SIAPE_instituidora diferente do conteúdo do JSON",
        )

    # Validações do esquema
    try:
        novo_plano_trabalho = schemas.PlanoTrabalhoSchema.model_validate(plano_trabalho)
    except Exception as exception:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=json.loads(e.json())
        ) from exception

    # Verifica se já existe
    db_plano_trabalho = await crud.get_plano_trabalho(
        db_session=db,
        cod_SIAPE_instituidora=cod_SIAPE_instituidora,
        id_plano_trabalho_participante=id_plano_trabalho_participante,
    )

    if not db_plano_trabalho:  # create
        crud.create_plano_trabalho(
            db_session=db,
            cod_SIAPE_instituidora=cod_SIAPE_instituidora,
            plano_trabalho=novo_plano_trabalho,
        )
    else:  # update
        crud.update_plano_trabalho(
            db_session=db,
            cod_SIAPE_instituidora=cod_SIAPE_instituidora,
            plano_trabalho=novo_plano_trabalho,
        )
    return novo_plano_trabalho


@app.get(
    "/organizacao/{cod_SIAPE_instituidora}/plano_entrega/{id_plano_entrega_unidade}",
    summary="Consulta plano de entregas",
    response_model=schemas.PlanoEntregaSchema,
    tags=["plano de entregas"],
)
async def get_plano_entrega(
    id_plano_entrega_unidade: int,
    db: Session = Depends(get_db),
    user: FiefUserInfo = Depends(auth_backend.current_user()),
):
    "Consulta o plano de entregas com o código especificado."
    db_plano_entrega = await crud.get_plano_entrega(
        db_session=db,
        cod_SIAPE_instituidora=user["fields"]["cod_SIAPE_instituidora"],
        id_plano_entrega_unidade=id_plano_entrega_unidade,
    )
    if not db_plano_entrega:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Plano de entregas não encontrado"
        )
    # plano_trabalho = schemas.PlanoTrabalhoSchema.model_validate(db_plano_trabalho.__dict__)
    return db_plano_entrega.__dict__


@app.get(
    "/organizacao/{cod_SIAPE_instituidora}/participante/{cpf_participante}",
    summary="Consulta Status do Participante",
    response_model=schemas.StatusParticipanteSchema,
    tags=["status participante"],
)
async def get_status_participante(
    cpf_participante: str,
    db: Session = Depends(get_db),
    user: FiefUserInfo = Depends(auth_backend.current_user()),
):
    "Consulta o status do participante a partir da matricula SIAPE."
    db_status_participante = await crud.get_status_participante(
        db_session=db,
        cod_SIAPE_instituidora=user["fields"]["cod_SIAPE_instituidora"],
        cpf_participante=cpf_participante,
    )
    if not db_status_participante:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Status de Participante não encontrado"
        )

    return db_status_participante.__dict__



# @app.patch(
#     "/plano_trabalho/{cod_plano}",
#     summary="Atualiza plano de trabalho",
#     response_model=schemas.PlanoTrabalhoSchema,
# )
# async def patch_plano_trabalho(
#     cod_plano: str,
#     plano_trabalho: schemas.PlanoTrabalhoUpdateSchema,
#     db: Session = Depends(get_db),
#     user: User = Depends(auth_backend.authenticated(scope=["openid", "required_scope"])),
# ):
#     "Atualiza um plano de trabalho existente nos campos informados."
#     # Validações da entrada conforme regras de negócio
#     if cod_plano != plano_trabalho.cod_plano:
#         raise HTTPException(
#             status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail="Parâmetro cod_plano diferente do conteúdo do JSON",
#         )

#     db_plano_trabalho = crud.get_plano_trabalho(db, user.cod_unidade, cod_plano)
#     if db_plano_trabalho is None:
#         raise HTTPException(
#             status.HTTP_404_NOT_FOUND,
#             detail="Só é possível aplicar PATCH em um recurso" + " existente.",
#         )
#     if db_plano_trabalho.cod_unidade != user.cod_unidade:
#         raise HTTPException(
#             status.HTTP_403_FORBIDDEN,
#             detail="Usuário não pode alterar Plano de Trabalho" + " de outra unidade.",
#         )

#     # atualiza os atributos, exceto atividades
#     merged_plano_trabalho = util.sa_obj_to_dict(db_plano_trabalho)
#     plano_trabalho_patch = plano_trabalho.dict(exclude_unset=True)
#     if plano_trabalho_patch.get("atividades", None):
#         del plano_trabalho_patch["atividades"]
#     merged_plano_trabalho.update(plano_trabalho_patch)

#     # atualiza as atividades

#     # traz a lista de atividades que está no banco
#     db_atividades = util.list_to_dict(
#         [
#             util.sa_obj_to_dict(atividade)
#             for atividade in getattr(db_plano_trabalho, "atividades", list())
#         ],
#         "id_atividade",
#     )

#     # cada atividade a ser modificada
#     patch_atividades = util.list_to_dict(
#         plano_trabalho.dict(exclude_unset=True).get("atividades", list()),
#         "id_atividade",
#     )

#     merged_atividades = util.merge_dicts(db_atividades, patch_atividades)
#     merged_plano_trabalho["atividades"] = util.dict_to_list(
#         merged_atividades, "id_atividade"
#     )

#     # tenta validar o esquema

#     # para validar o esquema, é necessário ter o atributo atividades,
#     # mesmo que seja uma lista vazia
#     if merged_plano_trabalho.get("atividades", None) is None:
#         merged_plano_trabalho["atividades"] = []
#     # valida o esquema do plano de trabalho atualizado
#     try:
#         merged_schema = schemas.PlanoTrabalhoSchema(**merged_plano_trabalho)
#     except ValidationError as e:
#         raise HTTPException(
#             status.HTTP_422_UNPROCESSABLE_ENTITY, detail=json.loads(e.json())
#         ) from e

#     crud.update_plano_trabalho(db, merged_schema, user.cod_unidade)
#     return merged_plano_trabalho


# Esconde alguns métodos da interface OpenAPI
def public_facing_openapi():
    "Cria o esquema da OpenAPI disponível ao público externo."
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        description=app.description,
        version=app.version,
        routes=app.routes,
    )
    # paths = openapi_schema["paths"]
    # del paths["/truncate_pts_atividades"]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = public_facing_openapi
