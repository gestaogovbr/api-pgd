"""
Testes relacionados ao plano de trabalho do participante.
"""
import itertools

from httpx import Client

from fastapi import status

import pytest


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
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    """Cria um novo Plano de Trabalho do Participante, em uma unidade
    na qual ele está autorizado, contendo todos os dados necessários.
    """
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == input_pt


def test_create_plano_trabalho_unidade_nao_permitida(
    input_pt: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    """Tenta criar um novo Plano de Trabalho do Participante, em uma
    organização na qual ele não está autorizado.
    """
    response = client.put(
        f"/organizacao/2"  # só está autorizado na organização 1
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json().get("detail", None) == "Usuário sem permissão na unidade."


def test_update_plano_trabalho(
    input_pt: dict,
    example_pt,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    """Atualiza um Plano de Trabalho existente usando o método PUT."""
    # A fixture example_pt cria um novo Plano de Trabalho na API
    # Altera um campo do PT e reenvia pra API (update)
    input_pt["cod_SIAPE_unidade_exercicio"] = 100  # Valor era 99
    client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )
    # Consulta API para conferir se a alteração foi persistida
    response = client.get("/plano_trabalho/555", headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nome_unidade_exercicio"] == "CGINF"


@pytest.mark.parametrize(
    "tipo_contribuicao, id_entrega",
    [
        (1, 1),
        (1, 2),
        (1, None),
        (2, 1),
        (2, None),
        (3, 1),
        (3, None),
    ],
)
def test_create_plano_trabalho_id_entrega_check(
    input_pt: dict,
    tipo_contribuicao: int,
    id_entrega: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    truncate_pt,
    example_pe,
    client: Client,
):
    """Tenta criar um novo plano de trabalho, sendo que, quando o campo
    tipo_contribuicao tiver valor 1, o campo id_entrega se tornará
    obrigatório.
    """
    input_pt["tipo_contribuicao"] = tipo_contribuicao
    input_pt["id_entrega"] = id_entrega
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if tipo_contribuicao == 1 and id_entrega is None:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json().get("detail", None) == "O campo id_entrega é"
            " obrigatório quando tipo_contribuicao tiver o valor 1."
        )
    else:
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == input_pt


@pytest.mark.parametrize("omitted_fields", enumerate(fields_consolidacao["optional"]))
def test_create_plano_trabalho_consolidacao_omit_optional_fields(
    input_pt: dict,
    omitted_fields: list,
    user1_credentials: dict,
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
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{input_pt['id_plano_trabalho_participante']}",
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
    user1_credentials: dict,
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
    example_pt = input_pt.copy()
    for field in field_list:
        del input_pt[field]

    input_pt["id_plano_trabalho_participante"] = (
        1800 + offset
    )  # precisa ser um novo plano
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{example_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_huge_plano_trabalho(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    def create_huge_atividade(id_atividade: str):
        new_atividade = input_pt["atividades"][0].copy()
        new_atividade["id_atividade"] = id_atividade
        new_atividade["entrega_esperada"] = "x" * 1000000  # 1mi de caracteres
        new_atividade["justificativa"] = "x" * 1000000  # 1mi de caracteres
        return new_atividade

    for i in range(200):
        input_pt["atividades"].append(create_huge_atividade(f"unique-key-{i}"))

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/555",
        json=input_pt,
        headers=header_usr_1,
    )

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
    user1_credentials: dict,
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

    input_pt["id_plano_trabalho_participante"] = 555  # precisa ser um plano existente
    call = getattr(client, verb)  # put ou patch
    response = call(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
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
    user1_credentials: dict,
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

    input_pt["id_plano_trabalho_participante"] = 999  # precisa ser um plano inexistente
    response = client.patch(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_pt_cod_plano_inconsistent(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["id_plano_trabalho_participante"] = 110
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/plano_trabalho/111",
        json=input_pt,
        headers=header_usr_1,  # diferente de 110
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = (
        "Parâmetro id_plano_trabalho_participante diferente do conteúdo do JSON"
    )
    assert response.json().get("detail", None) == detail_msg


def test_get_plano_trabalho(
    user1_credentials: dict, header_usr_1: dict, truncate_pt, example_pt, client: Client
):
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/plano_trabalho/555",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_pt_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/plano_trabalho/888888888",
        headers=header_usr_1,
    )
    assert response.status_code == 404

    assert response.json().get("detail", None) == "Plano de trabalho não encontrado"


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, data_inicio_plano, data_termino_plano",
    [
        (77, "2020-06-04", "2020-04-01"),
        (78, "2020-06-04", "2020-04-01"),
        (79, "2020-06-04", "2020-04-01"),
    ],
)
def test_create_pt_invalid_dates(
    input_pt: dict,
    id_plano_trabalho_participante: str,
    data_inicio_plano: str,
    data_termino_plano: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["data_inicio_plano"] = data_inicio_plano
    input_pt["data_termino_plano"] = data_termino_plano
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )
    if data_inicio_plano > data_termino_plano:
        assert response.status_code == 422
        detail_msg = (
            "Data fim do Plano de Trabalho deve ser maior"
            " ou igual que Data de início."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, data_inicio_plano, data_termino_plano, "
    "data_inicio_registro, data_fim_registro",
    [
        (80, "2023-06-04", "2023-06-11", "2023-04-01", "2023-04-02"),
        (81, "2023-06-04", "2023-06-11", "2024-04-01", "2023-04-02"),
        (82, "2023-06-04", "2023-06-11", "2021-04-02", "2023-06-02"),
        (83, "2023-04-01", "2023-04-01", "2023-06-01", "2023-06-02"),
        (84, "2023-04-01", "2023-04-01", "2023-04-01", "2023-04-01"),
    ],
)
def test_create_pt_invalid_data_avaliacao(
    input_pt: dict,
    id_plano_trabalho_participante: int,
    data_inicio_plano: str,
    data_termino_plano: str,
    data_inicio_registro: str,
    data_fim_registro: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["data_inicio_plano"] = data_inicio_plano
    input_pt["data_termino_plano"] = "2025-01-01"
    input_pt["consolidacoes"][0]["data_inicio_registro"] = data_inicio_registro
    input_pt["consolidacoes"][0]["data_fim_registro"] = data_fim_registro

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )
    if (
        data_inicio_plano > data_inicio_registro
        or data_inicio_plano > data_fim_registro
    ):
        assert response.status_code == 422
        detail_msg = (
            "Data de início e de fim de registro devem ser maiores ou iguais"
            " que a Data de início do Plano de Trabalho."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, id_ent_1, id_ent_2",
    [
        (90, 401, 402),
        (91, 403, 403),  # <<<< IGUAIS
        (92, 404, 404),  # <<<< IGUAIS
        (93, 405, 406),
    ],
)
def test_create_pt_duplicate_contribuicao(
    input_pt: dict,
    id_plano_entrega_unidade: int,
    id_ent_1: int,
    id_ent_2: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    """Tenta criar um plano de trabalho com contribuições com
      id_entrega duplicados
    TODO: Validar RN  - Pode existir contribuições com entregas com mesmo id?"""

    input_pt["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    input_pt["contribuicoes"][0]["id_entrega"] = id_ent_1
    input_pt["contribuicoes"][1]["id_entrega"] = id_ent_2

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )
    if id_ent_1 == id_ent_2:
        assert response.status_code == 422
        detail_msg = "Contribuições devem possuir id_entrega diferentes."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, cpf",
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
    id_plano_trabalho_participante: str,
    cpf: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["cpf"] = cpf

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
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
    "id_plano_trabalho_participante, modalidade_execucao",
    [
        (80, -1),
        (81, -2),
        (82, -3),
        (83, -0),
        (84, 4),
        (85, 1),
    ],
)
def test_create_pt_invalid_modalidade_execucao(
    input_pt: dict,
    id_plano_trabalho_participante: int,
    modalidade_execucao: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["modalidade_execucao"] = modalidade_execucao
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )

    if modalidade_execucao in (1, 2, 3):
        assert response.status_code == status.HTTP_200_OK
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = "Value is not a valid enumeration member; permitted: 1, 2, 3"
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
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    id_plano_trabalho_participante = "767676"
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["carga_horaria_semanal"] = carga_horaria_semanal
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Carga horária semanal deve ser entre 1 e 40"
    assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize(
    "tipo_contribuicao, horas_vinculadas",
    [
        (None, 40),
        (1, None),
        (2, None),
        (3, None),
    ],
)
def test_create_pt_missing_mandatory_fields_contribuicoes(
    input_pt: dict,
    tipo_contribuicao: int,
    horas_vinculadas: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    id_plano_trabalho_participante = "111222333"
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["contribuicoes"] = {
        "tipo_contribuicao": tipo_contribuicao,
        "horas_vinculadas": horas_vinculadas,
    }

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, tipo_contribuicao, id_plano_entrega_unidade, id_entrega",
    [
        (120, 1, None, None),
        (121, 1, 1, 1),
        (121, 1, 1, 999),  # id_entrega não existente
        (122, 1, 999, 1),  # id_plano_entrega_unidade não existente
        (123, 2, None, None),
        (124, 2, 1, 1),
        (125, 3, None, None),
        (126, 3, 1, 1),
    ],
)
def test_create_pt_contribuicoes_tipo_contribuicao_conditional_id_entrega(
    input_pt: dict,
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    id_plano_trabalho_participante: int,
    tipo_contribuicao: int,
    id_plano_entrega_unidade: int,
    id_entrega: int,
    truncate_pt,
    truncate_pe,
    client: Client,
):
    """Verifica o comportamento da API em relação à obrigatoriedade
    do campo id_entrega, a depender do valor de tipo_contribuicao.

    Se tipo_contribuicao == 1, então id_plano_entrega_unidade e
    id_entrega são obrigatórios e devem se referir a uma entrega
    existente de um plano de entregas existente.

    Se tipo_contribuicao == 2, então id_plano_entrega_unidade e
    id_entrega não devem ser informados.
    """
    # cria o plano de entrega 1, que deve ser existente como
    # premissa para o teste
    id_plano_entrega_existente = 1
    ids_entregas_existentes = [
        entrega["id_entrega"] for entrega in input_pe["entregas"]
    ]

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{id_plano_entrega_existente}",
        json=input_pe,
        headers=header_usr_1,
    )

    # Prepara o plano de trabalho com os parâmetros informados no teste
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
    input_pt["contribuicoes"][0]["id_entrega"] = id_entrega

    assert response.status_code == status.HTTP_200_OK

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )

    if tipo_contribuicao == 1:
        if not (id_plano_entrega_unidade and id_entrega):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "É necessário informar id_plano_entrega_unidade "
                "e id_entrega quando tipo_contribuicao == 1"
            )
            assert response.json().get("detail")[0]["msg"] == detail_msg
        elif (
            id_plano_entrega_unidade != id_plano_entrega_existente
            or id_entrega not in ids_entregas_existentes
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "Referência a entrega não encontrada"
            )
            assert response.json().get("detail")[0]["msg"] == detail_msg
    elif tipo_contribuicao == 2 and (id_plano_entrega_unidade or id_entrega):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = (
            "Não se deve informar id_plano_entrega_unidade nem "
            "id_entrega quando tipo_contribuicao == 2"
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


def test_create_pt_duplicate_cod_plano(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    truncate_pt,
    client: Client,
):
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/555",
        json=input_pt,
        headers=header_usr_1,
    )
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/555",
        json=input_pt,
        headers=header_usr_2,
    )
    print(response.json().get("detail", None))

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_pt


@pytest.mark.parametrize("horas_homologadas", [(-1), (0)])
def test_create_pt_invalid_horas_homologadas(
    input_pt: dict,
    horas_homologadas: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,
    client: Client,
):
    id_plano_trabalho_participante = "138"
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["horas_homologadas"] = horas_homologadas
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Horas homologadas devem ser maior que zero"
    assert response.json().get("detail")[0]["msg"] == detail_msg
