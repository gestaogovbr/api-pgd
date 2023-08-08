"""The api.py module defines all the routes for the API.
"""

from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status, Header
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fief_client import FiefUserInfo
from sqlalchemy.orm import Session

import schemas, crud
from users import (
    get_db,
    auth_backend,
    create_db_and_tables,
)

with open("docs/description.md", "r", encoding="utf-8") as f:
    description = f.read()

app = FastAPI(
    title="Plataforma de recebimento de dados do Programa de Gestão - PGD",
    description=description,
    version="0.2.0",
)

@app.get("/user")
async def get_user(
    user: FiefUserInfo = Depends(
        auth_backend.current_user()
    ),
):
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


# @app.put(
#     "/plano_trabalho/{cod_plano}",
#     summary="Cria ou substitui plano de trabalho",
#     response_model=schemas.PlanoTrabalhoSchema,
# )
# async def create_or_update_plano_trabalho(
#     cod_plano: str,
#     plano_trabalho: schemas.PlanoTrabalhoSchema,
#     db: Session = Depends(get_db),
#     user: User = Depends(auth_backend.authenticated(scope=["openid", "required_scope"])),
# ):
#     """Cria um novo plano de trabalho ou, se existente, substitui um
#     plano de trabalho por um novo com os dados informados."""
#     # Validações da entrada conforme regras de negócio
#     if cod_plano != plano_trabalho.cod_plano:
#         raise HTTPException(
#             status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail="Parâmetro cod_plano diferente do conteúdo do JSON",
#         )

#     db_plano_trabalho = crud.get_plano_trabalho(db, user.cod_unidade, cod_plano)
#     if db_plano_trabalho is None:  # create
#         try:
#             novo_plano_trabalho = schemas.PlanoTrabalhoSchema(**plano_trabalho.dict())
#             crud.create_plano_tabalho(db, novo_plano_trabalho, user.cod_unidade)
#         except ValidationError as e:
#             raise HTTPException(
#                 status.HTTP_422_UNPROCESSABLE_ENTITY, detail=json.loads(e.json())
#             ) from e
#     else:  # update
#         if db_plano_trabalho.cod_unidade == user.cod_unidade:
#             crud.update_plano_trabalho(db, plano_trabalho, user.cod_unidade)
#         else:
#             raise HTTPException(
#                 status.HTTP_403_FORBIDDEN,
#                 detail="Usuário não pode alterar Plano de Trabalho"
#                 + " de outra unidade.",
#             )
#     return plano_trabalho


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


@app.get(
    "/plano_trabalho/{cod_plano}",
    summary="Consulta plano de trabalho",
    response_model=schemas.PlanoTrabalhoSchema,
)
async def get_plano_trabalho(
    cod_plano: str,
    db: Session = Depends(get_db),
    user: FiefUserInfo = Depends(
        auth_backend.current_user()
    ),
):
    "Consulta o plano de trabalho com o código especificado."
    db_plano_trabalho = await crud.get_plano_trabalho(db, user["fields"]["cod_unidade"], cod_plano)
    if db_plano_trabalho is None:
        raise HTTPException(404, detail="Plano de trabalho não encontrado")
    plano_trabalho = schemas.PlanoTrabalhoSchema.from_orm(db_plano_trabalho)
    return plano_trabalho.__dict__


# @app.post("/truncate_pts_atividades")
# async def truncate_pts_atividades(
#     db: Session = Depends(get_db),
#     user: User = Depends(api_users.current_user(active=True, superuser=True)),
# ):
#     crud.truncate_pts_atividades(db)


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
