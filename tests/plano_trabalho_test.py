"""
Testes relacionados ao plano de trabalho do participante.
"""
import itertools

from httpx import Client

from fastapi import status

import pytest

@pytest.fixture()
def input_pt() -> dict:
    """Template de Plano de Trabalho do Participante

    Returns:
        dict: template de exemplo
    """
    return {
        "cod_siape_insituidora": 99,
        "id_plano_trabalho_participante": 1,
        "id_plano_entrega_unidade": 1,
        "cod_SIAPE_unidade_exercicio": 99,
        "cpf_participante": 99160773120,
        "data_início_plano": "2023-01-01",
        "data_termino_plano": "2023-01-15",
        "carga_horaria_total_periodo_plano": 80,
        "contribuicoes": [
            {"tipo_contribuicao": 1, "id_entrega": 1, "horas_vinculadas_entrega": 40},
            {"tipo_contribuicao": 2, "horas_vinculadas_entrega": 40},
        ],
        "consolidacoes": [
            {
                "data_inicio_registro": "2023-01-01",
                "data_fim_registro": "2023-02-01",
                "avaliacao_plano_trabalho": 5,
            },
        ],
    }

# grupos de campos opcionais e obrigatórios a testar

fields_plano_trabalho = {
    "mandatory": (
        ["id_plano_entrega_unidade"],
        ["cod_SIAPE_unidade_exercicio"],
        ["cpf_participante"],
        ["data_inicio_plano"],
        ["data_termino_plano"],
        ["carga_horaria_total_periodo_plano"],
        ["contribuicoes"],
        ["consolidacoes"],
    )
}

fields_contribuicao = {
    "optional": (["id_entrega"],),
    "mandatory": (
        ["id_plano_trabalho_participante"],
        ["tipo_contribuicao"],
        ["horas_vinculadas_entrega"],
    ),
}

fields_consolidacao = {
    "optional": (["avaliacao_plano_trabalho"],),
    "mandatory": (
        ["data_inicio_registro"],
        ["data_fim_registro"],
    ),
}


def test_create_plano_trabalho_completo(
    input_pt: dict, header_usr_1: dict, truncate_pt, client: Client
):
    response = client.put(f"/plano_trabalho/555", json=input_pt, headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_pt


def test_update_plano_trabalho(
    input_pt: dict, example_pt, header_usr_1: dict, truncate_pt, client: Client
):
    # A fixture example_pt cria um novo Plano de Trabalho na API
    # Altera um campo do PT e reenvia pra API (update)
    input_pt["nome_unidade_exercicio"] = "CGINF"  # Valor era "string"
    client.put("/plano_trabalho/555", json=input_pt, headers=header_usr_1)
    # Consulta API para conferir se a alteração foi persistida
    response = client.get("/plano_trabalho/555", headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nome_unidade_exercicio"] == "CGINF"


@pytest.mark.parametrize("omitted_fields", enumerate(fields_contribuicao["optional"]))
def test_create_plano_trabalho_contribuicao_omit_optional_fields(
    input_pt: dict,
    omitted_fields: list,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um novo plano de trabalho, omitindo campos opcionais
    nas entregas.
    """

    offset, field_list = omitted_fields
    for field in field_list:
        for contribuicao in input_pt["contribuicoes"]:
            if field in contribuicao:
                del contribuicao[field]

    input_pt["id_plano_entrega_unidade"] = 557 + offset
    response = client.put(
        f"/plano_trabalho/{input_pt['cod_SIAPE_instituidora']}/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("omitted_fields", enumerate(fields_consolidacao["optional"]))
def test_create_plano_trabalho_consolidacao_omit_optional_fields(
    input_pt: dict,
    omitted_fields: list,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um novo plano de entregas omitindo campos opcionais"""

    offset, field_list = omitted_fields
    for field in field_list:
        for consolidacao in input_pt["consolidacoes"]:
            if field in consolidacao:
                del consolidacao[field]

    input_pt["id_plano_entrega_unidade"] = 557 + offset
    response = client.put(
        f"/plano_entrega/{input_pt['cod_SIAPE_instituidora']}/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "missing_fields", enumerate(fields_plano_trabalho["mandatory"])
)
def test_create_plano_trabalho_missing_mandatory_fields(
    input_pt: dict,
    missing_fields: list,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    """Tenta criar um plano de trabalho, faltando campos obrigatórios.
    Tem que ser um plano de trabalho novo, pois na atualização de um
    plano de trabalho existente, o campo que ficar faltando será
    interpretado como um campo que não será atualizado, ainda que seja
    obrigatório para a criação.
    """
    offset, field_list = missing_fields
    for field in field_list:
        del input_pt[field]

    input_pt["cod_plano"] = 1800 + offset  # precisa ser um novo plano
    response = client.put(
        f"/plano_trabalho/{input_pt['cod_plano']}", json=input_pt, headers=header_usr_1
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_huge_plano_trabalho(
    input_pt: dict, header_usr_1: dict, truncate_pt, client: Client
):
    def create_huge_atividade(id_atividade: str):
        new_atividade = input_pt["atividades"][0].copy()
        new_atividade["id_atividade"] = id_atividade
        new_atividade["entrega_esperada"] = "x" * 1000000  # 1mi de caracteres
        new_atividade["justificativa"] = "x" * 1000000  # 1mi de caracteres
        return new_atividade

    for i in range(200):
        input_pt["atividades"].append(create_huge_atividade(f"unique-key-{i}"))

    response = client.put(f"/plano_trabalho/555", json=input_pt, headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "verb, missing_fields",
    itertools.product(  # todas as combinações entre
        ("put", "patch"), fields_plano_trabalho["mandatory"]  # verb  # missing_fields
    ),
)
def test_update_plano_trabalho_missing_mandatory_fields(
    truncate_pt,
    verb: str,
    example_pt,
    input_pt: dict,
    missing_fields: list,
    header_usr_1: dict,
    client: Client,
):
    """Tenta atualizar um plano de trabalho faltando campos
    obrigatórios.

    Para usar o verbo PUT é necessário passar a representação completa
    do recurso. Por isso, os campos obrigatórios não podem estar
    faltando. Para realizar uma atualização parcial, use o método PATCH.

    Já com o verbo PATCH, os campos omitidos são interpretados como sem
    alteração. Por isso, é permitido omitir os campos obrigatórios.
    """
    for field in missing_fields:
        del input_pt[field]

    input_pt["cod_plano"] = 555  # precisa ser um plano existente
    call = getattr(client, verb)  # put ou patch
    response = call(
        f"/plano_trabalho/{input_pt['cod_plano']}", json=input_pt, headers=header_usr_1
    )
    if verb == "put":
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    elif verb == "patch":
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("missing_fields", fields_plano_trabalho["mandatory"])
def test_patch_plano_trabalho_inexistente(
    truncate_pt,
    input_pt: dict,
    missing_fields: list,
    header_usr_1: dict,
    client: Client,
):
    """Tenta atualizar um plano de trabalho com PATCH, faltando campos
    obrigatórios.

    Com o verbo PATCH, os campos omitidos são interpretados como sem
    alteração. Por isso, é permitido omitir os campos obrigatórios.
    """
    for field in missing_fields:
        del input_pt[field]

    input_pt["cod_plano"] = 999  # precisa ser um plano inexistente
    response = client.patch(
        f"/plano_trabalho/{input_pt['cod_plano']}", json=input_pt, headers=header_usr_1
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_pt_cod_plano_inconsistent(
    input_pt: dict, header_usr_1: dict, truncate_pt, client: Client
):
    input_pt["cod_plano"] = 110
    response = client.put(
        "/plano_trabalho/111", json=input_pt, headers=header_usr_1  # diferente de 110
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro cod_plano diferente do conteúdo do JSON"
    assert response.json().get("detail", None) == detail_msg


def test_get_plano_trabalho(
    header_usr_1: dict, truncate_pt, example_pt, client: Client
):
    response = client.get("/plano_trabalho/555", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK


def test_get_pt_inexistente(header_usr_1: dict, client: Client):
    response = client.get("/plano_trabalho/888888888", headers=header_usr_1)
    assert response.status_code == 404

    assert response.json().get("detail", None) == "Plano de trabalho não encontrado"


@pytest.mark.parametrize(
    "data_inicio, data_fim, cod_plano, id_ati_1, id_ati_2",
    [
        ("2020-06-04", "2020-04-01", "77", 333, 334),
        ("2020-06-04", "2020-04-01", "78", 335, 336),
        ("2020-06-04", "2020-04-01", "79", 337, 338),
    ],
)
def test_create_pt_invalid_dates(
    input_pt: dict,
    data_inicio: str,
    data_fim: str,
    cod_plano: str,
    id_ati_1: str,
    id_ati_2: str,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["data_inicio"] = data_inicio
    input_pt["data_fim"] = data_fim
    input_pt["cod_plano"] = cod_plano
    input_pt["atividades"][0]["id_atividade"] = id_ati_1
    input_pt["atividades"][1]["id_atividade"] = id_ati_2

    response = client.put(
        f"/plano_trabalho/{cod_plano}", json=input_pt, headers=header_usr_1
    )
    if data_inicio > data_fim:
        assert response.status_code == 422
        detail_msg = (
            "Data fim do Plano de Trabalho deve ser maior"
            " ou igual que Data de início."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "dt_inicio, dt_avaliacao_1, dt_avaliacao_2, cod_plano, id_ati_1, id_ati_2",
    [
        ("2020-06-04", "2020-04-01", "2020-04-01", "77", 333, 334),
        ("2020-06-04", "2020-04-01", "2021-04-01", "78", 335, 336),
        ("2020-06-04", "2020-04-01", "2019-04-01", "79", 337, 338),
        ("2020-04-01", "2020-04-01", "2020-06-04", "80", 339, 340),
        ("2020-04-01", "2020-04-01", "2020-04-01", "81", 341, 342),
        ("2020-04-01", "2020-02-01", "2020-01-04", "82", 343, 344),
    ],
)
def test_create_pt_invalid_data_avaliacao(
    input_pt: dict,
    dt_inicio: str,
    dt_avaliacao_1: str,
    dt_avaliacao_2: str,
    cod_plano: dict,
    id_ati_1: str,
    id_ati_2: str,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["data_inicio"] = dt_inicio
    input_pt["data_fim"] = "2025-01-01"
    input_pt["cod_plano"] = cod_plano
    input_pt["atividades"][0]["id_atividade"] = id_ati_1
    input_pt["atividades"][0]["data_avaliacao"] = dt_avaliacao_1
    input_pt["atividades"][1]["id_atividade"] = id_ati_2
    input_pt["atividades"][1]["data_avaliacao"] = dt_avaliacao_2

    response = client.put(
        f"/plano_trabalho/{cod_plano}", json=input_pt, headers=header_usr_1
    )
    if dt_inicio > dt_avaliacao_1 or dt_inicio > dt_avaliacao_2:
        assert response.status_code == 422
        detail_msg = (
            "Data de avaliação da atividade deve ser maior ou igual"
            " que a Data de início do Plano de Trabalho."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "cod_plano, id_ati_1, id_ati_2",
    [
        ("90", 401, 402),
        ("91", 403, 403),  # <<<< IGUAIS
        ("92", 404, 404),  # <<<< IGUAIS
        ("93", 405, 406),
    ],
)
def test_create_pt_duplicate_atividade(
    input_pt: dict,
    cod_plano: str,
    id_ati_1: str,
    id_ati_2: str,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["cod_plano"] = cod_plano
    input_pt["atividades"][0]["id_atividade"] = id_ati_1
    input_pt["atividades"][1]["id_atividade"] = id_ati_2

    response = client.put(
        f"/plano_trabalho/{cod_plano}", json=input_pt, headers=header_usr_1
    )
    if id_ati_1 == id_ati_2:
        assert response.status_code == 422
        detail_msg = "Atividades devem possuir id_atividade diferentes."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "cod_plano, cpf",
    [
        ("100", "11111111111"),
        ("101", "22222222222"),
        ("102", "33333333333"),
        ("103", "44444444444"),
        ("104", "04811556435"),
        ("103", "444-444-444.44"),
        ("108", "-44444444444"),
        ("111", "444444444"),
        ("112", "-444 4444444"),
        ("112", "4811556437"),
        ("112", "048115564-37"),
        ("112", "04811556437     "),
        ("112", "    04811556437     "),
        ("112", ""),
    ],
)
def test_create_pt_invalid_cpf(
    input_pt: dict,
    cod_plano: str,
    cpf: str,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["cod_plano"] = cod_plano
    input_pt["cpf"] = cpf

    response = client.put(
        f"/plano_trabalho/{cod_plano}", json=input_pt, headers=header_usr_1
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = [
        "Digitos verificadores do CPF inválidos.",
        "CPF inválido.",
        "CPF precisa ter 11 digitos.",
        "CPF deve conter apenas digitos.",
    ]
    assert response.json().get("detail")[0]["msg"] in detail_msg


@pytest.mark.parametrize(
    "cod_plano, modalidade_execucao", [("556", -1), ("81", -2), ("82", -3)]
)
def test_create_pt_invalid_modalidade_execucao(
    input_pt: dict,
    cod_plano: str,
    modalidade_execucao: int,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["cod_plano"] = cod_plano
    input_pt["modalidade_execucao"] = modalidade_execucao
    response = client.put(
        f"/plano_trabalho/{cod_plano}", json=input_pt, headers=header_usr_1
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "value is not a valid enumeration member; permitted: 1, 2, 3"
    assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize(
    "carga_horaria_semanal",
    [
        (56),
        (-2),
        (0),
    ],
)
def test_create_pt_invalid_carga_horaria_semanal(
    input_pt: dict,
    carga_horaria_semanal: int,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    cod_plano = "767676"
    input_pt["cod_plano"] = cod_plano
    input_pt["carga_horaria_semanal"] = carga_horaria_semanal
    response = client.put(
        f"/plano_trabalho/{cod_plano}", json=input_pt, headers=header_usr_1
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Carga horária semanal deve ser entre 1 e 40"
    assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize(
    "id_atividade, nome_atividade, faixa_complexidade, "
    "tempo_presencial_estimado, tempo_presencial_programado, "
    "tempo_teletrabalho_estimado, tempo_teletrabalho_programado",
    [
        (None, "asd", "asd", 0.0, 0.0, 0.0, 0.0),
        ("123123", None, "asd", 0.0, 0.0, 0.0, 0.0),
        ("123123", "asd", None, 0.0, 0.0, 0.0, 0.0),
        ("123123", "asd", "asd", None, 0.0, 0.0, 0.0),
        ("123123", "asd", "asd", 0.0, None, 0.0, 0.0),
        ("123123", "asd", "asd", 0.0, 0.0, None, 0.0),
        ("123123", "asd", "asd", 0.0, 0.0, 0.0, None),
    ],
)
def test_create_pt_missing_mandatory_fields_atividade(
    input_pt: dict,
    id_atividade: str,
    nome_atividade: str,
    faixa_complexidade: str,
    tempo_presencial_estimado: float,
    tempo_presencial_programado: float,
    tempo_teletrabalho_estimado: float,
    tempo_teletrabalho_programado: float,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    cod_plano = "111222333"
    input_pt["cod_plano"] = cod_plano
    input_pt["atividades"][0]["id_atividade"] = id_atividade
    input_pt["atividades"][0]["nome_atividade"] = nome_atividade
    input_pt["atividades"][0]["faixa_complexidade"] = faixa_complexidade
    input_pt["atividades"][0]["tempo_presencial_estimado"] = tempo_presencial_estimado
    input_pt["atividades"][0][
        "tempo_presencial_programado"
    ] = tempo_presencial_programado
    input_pt["atividades"][0][
        "tempo_teletrabalho_estimado"
    ] = tempo_teletrabalho_estimado
    input_pt["atividades"][0][
        "tempo_teletrabalho_programado"
    ] = tempo_teletrabalho_programado

    response = client.put(
        f"/plano_trabalho/{cod_plano}", json=input_pt, headers=header_usr_1
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "none is not an allowed value"
    assert response.json().get("detail")[0]["msg"] == detail_msg


def test_create_pt_duplicate_cod_plano(
    input_pt: dict, header_usr_1: dict, header_usr_2: dict, truncate_pt, client: Client
):
    response = client.put(f"/plano_trabalho/555", json=input_pt, headers=header_usr_1)
    response = client.put(f"/plano_trabalho/555", json=input_pt, headers=header_usr_2)
    print(response.json().get("detail", None))

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_pt


@pytest.mark.parametrize("horas_homologadas", [(-1), (0)])
def test_create_pt_invalid_horas_homologadas(
    input_pt: dict,
    horas_homologadas: int,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    cod_plano = "138"
    input_pt["cod_plano"] = cod_plano
    input_pt["horas_homologadas"] = horas_homologadas
    response = client.put(
        f"/plano_trabalho/{cod_plano}", json=input_pt, headers=header_usr_1
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Horas homologadas devem ser maior que zero"
    assert response.json().get("detail")[0]["msg"] == detail_msg
