"""
Testes relacionados à atividade.
"""

import itertools
from datetime import datetime

from requests import Session

from fastapi import status

import pytest

# grupos de campos opcionais e obrigatórios a testar

fields_atividade = {
    "optional": (
        ["nome_grupo_atividade"],
        ["parametros_complexidade"],
        ["entrega_esperada"],
        ["qtde_entregas_efetivas"],
        ["data_avaliacao"],
        ["justificativa"],
        ["tempo_presencial_executado"],
        ["tempo_teletrabalho_executado"],
    ),
    "mandatory": (
        ["nome_atividade"],
        ["faixa_complexidade"],
        ["tempo_presencial_estimado"],
        ["tempo_presencial_programado"],
        ["tempo_teletrabalho_estimado"],
        ["tempo_teletrabalho_programado"],
        ["qtde_entregas"],
    )
}

atividades_dict = {
    "2": {
        "nome_grupo_atividade": "string",
        "nome_atividade": "string",
        "faixa_complexidade": "string",
        "parametros_complexidade": "string",
        "tempo_presencial_estimado": 0.0,
        "tempo_presencial_programado": 0.0,
        "tempo_presencial_executado": None,
        "tempo_teletrabalho_estimado": 0.0,
        "tempo_teletrabalho_programado": 0.0,
        "tempo_teletrabalho_executado": None,
        "entrega_esperada": "string",
        "qtde_entregas": 0,
        "qtde_entregas_efetivas": 0,
        "avaliacao": 0,
        "data_avaliacao": "2021-01-15",
    "justificativa": "string"
    },
    "3": {
        "nome_grupo_atividade": "string",
        "nome_atividade": "string",
        "faixa_complexidade": "string",
        "parametros_complexidade": "string",
        "tempo_presencial_estimado": 0.0,
        "tempo_presencial_programado": 0.0,
        "tempo_presencial_executado": None,
        "tempo_teletrabalho_estimado": 0.0,
        "tempo_teletrabalho_programado": 0.0,
        "tempo_teletrabalho_executado": None,
        "entrega_esperada": "string",
        "qtde_entregas": 0,
        "qtde_entregas_efetivas": 0,
        "avaliacao": 0,
        "data_avaliacao": "2021-01-15",
        "justificativa": "string"
    }
}

@pytest.mark.parametrize("omitted_fields",
                         enumerate(fields_atividade["optional"]))
def test_create_atvidades_omit_optional_fields(input_pt: dict,
                                             omitted_fields: list,
                                             header_usr_1: dict,
                                             truncate_pt,
                                             client: Session):
    """Tenta criar um plano de trabalho, mas em cada atividade os
    campos opcionais são omitidos.
    """
    offset, field_list = omitted_fields
    for field in field_list:
        for atividade in input_pt["atividades"]:
            del atividade[field]

    input_pt["cod_plano"] = 557 + offset
    response = client.put(f"/plano_trabalho/{input_pt['cod_plano']}",
                          json=input_pt,
                          headers=header_usr_1)
    print(response.json())
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.parametrize("missing_fields",
                         enumerate(fields_atividade["mandatory"]))
def test_create_atividades_missing_mandatory_fields(input_pt: dict,
                                             missing_fields: list,
                                             header_usr_1: dict,
                                             truncate_pt,
                                             client: Session):
    """Tenta criar um plano de trabalho, mas em cada atividade os
    campos obrigatórios são omitidos.
    """
    offset, field_list = missing_fields
    for field in field_list:
        for atividade in input_pt["atividades"]:
            del atividade[field]

    input_pt["cod_plano"] = 1800 + offset # precisa ser um novo plano
    response = client.put(f"/plano_trabalho/{input_pt['cod_plano']}",
                          json=input_pt,
                          headers=header_usr_1)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.parametrize("verb, missing_fields",
                    itertools.product( # todas as combinações entre
                        ("put", "patch"), # verb
                        fields_atividade["mandatory"] # missing_fields
                    ))
def test_update_atividades_missing_mandatory_fields(verb: str,
                                            truncate_pt,
                                            example_pt,
                                            input_pt: dict,
                                            missing_fields: list,
                                            header_usr_1: dict,
                                            client: Session):
    """Tenta atualizar as atividades de um plano de trabalho faltando
    campos obrigatórios.

    Para usar o verbo PUT é necessário passar a representação completa
    do recurso. Por isso, os campos obrigatórios não podem estar
    faltando. Para realizar uma atualização parcial, use o método PATCH.

    Já com o verbo PATCH, os campos omitidos são interpretados como sem
    alteração. Por isso, é permitido omitir os campos obrigatórios.
    """
    for field in missing_fields:
        for atividade in input_pt["atividades"]:
            del atividade[field]

    input_pt["cod_plano"] = 555 # precisa ser um plano existente
    call = getattr(client, verb) # put ou patch
    response = call(f"/plano_trabalho/{input_pt['cod_plano']}",
                          json=input_pt,
                          headers=header_usr_1)
    if verb == "put":
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    elif verb == "patch":
        assert response.status_code == status.HTTP_200_OK

def test_substitute_atividades_list(truncate_pt,
                                    example_pt,
                                    input_pt: dict,
                                    header_usr_1: dict,
                                    client: Session):
    "Substitui a lista de atividades existentes por uma nova lista."
    input_pt["atividades"].pop() # remove a última atividade

    response = client.put(f"/plano_trabalho/{input_pt['cod_plano']}",
                            json=input_pt,
                            headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == input_pt

def test_append_atividades_list(truncate_pt,
                                example_pt,
                                input_pt: dict,
                                header_usr_1: dict,
                                client: Session):
    "Acrescenta uma nova atividade à lista de atividades existentes."
    nova_atividade = {
      "id_atividade": "4",
      "nome_grupo_atividade": "string",
      "nome_atividade": "string",
      "faixa_complexidade": "string",
      "parametros_complexidade": "string",
      "tempo_presencial_estimado": 0.0,
      "tempo_presencial_programado": 0.0,
      "tempo_presencial_executado": None,
      "tempo_teletrabalho_estimado": 0.0,
      "tempo_teletrabalho_programado": 0.0,
      "tempo_teletrabalho_executado": None,
      "entrega_esperada": "string",
      "qtde_entregas": 0,
      "qtde_entregas_efetivas": 0,
      "avaliacao": 0,
      "data_avaliacao": "2021-02-15",
      "justificativa": "string"
    }

    patch_input = {
        "cod_plano": input_pt["cod_plano"],
        "atividades": [nova_atividade]
    }

    response = client.patch(f"/plano_trabalho/{input_pt['cod_plano']}",
                            json=patch_input,
                            headers=header_usr_1)

    input_pt["atividades"].append(nova_atividade)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == input_pt

@pytest.mark.parametrize("verb, data_avaliacao",
                            itertools.product(
                                ("put", "patch"),
                                (
                                    "2021-01-02", # é "<" data_inicio do plano
                                    "2021-03-01"
                                )
                            )
                        )
def test_modify_atividade(truncate_pt,
                            example_pt,
                            verb: str,
                            data_avaliacao: str,
                            input_pt: dict,
                            header_usr_1: dict,
                            client: Session):
    "Modifica uma atividade existente com put e patch."
    atividade = input_pt["atividades"][-1] # pega a última atividade
    atividade["data_avaliacao"] = data_avaliacao

    if verb == "put":
        response = client.put(f"/plano_trabalho/{input_pt['cod_plano']}",
                          json=input_pt,
                          headers=header_usr_1)
    elif verb == "patch":
        atividade_patch = {
            "cod_plano": input_pt["cod_plano"],
            "atividades": [
                {
                    "id_atividade": "3",
                    "data_avaliacao": data_avaliacao
                }
            ]
        }
        response = client.patch(f"/plano_trabalho/{input_pt['cod_plano']}",
                          json=atividade_patch,
                          headers=header_usr_1)

    if datetime.fromisoformat(data_avaliacao) < datetime.fromisoformat(
                                                    input_pt["data_inicio"]):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = "Data de avaliação da atividade deve ser maior ou igual" \
                     " que a Data de início do Plano de Trabalho."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == input_pt

