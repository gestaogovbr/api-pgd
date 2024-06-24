"""
Testes relacionados ao Plano de Entregas da Unidade
"""

from httpx import Client
from fastapi import status as http_status

import pytest

from util import over_a_year, assert_error_message

# constantes

STR_MAX_SIZE = 300

# grupos de campos opcionais e obrigatórios a testar

FIELDS_PLANO_ENTREGAS = {
    "optional": (
        ["avaliacao"],
        ["data_avaliacao"],
    ),
    "mandatory": (
        ["origem_unidade"],
        ["cod_unidade_autorizadora"],
        ["cod_unidade_instituidora"],
        ["cod_unidade_executora"],
        ["id_plano_entregas"],
        ["status"],
        ["data_inicio"],
        ["data_termino"],
        ["entregas"],
    ),
}

FIELDS_ENTREGA = {
    "optional": (["entrega_cancelada"],),
    "mandatory": (
        ["id_entrega"],
        ["nome_entrega"],
        ["meta_entrega"],
        ["tipo_meta"],
        ["data_entrega"],
        ["nome_unidade_demandante"],
        ["nome_unidade_destinataria"],
    ),
}


# Helper functions


def assert_equal_plano_entregas(plano_entregas_1: dict, plano_entregas_2: dict):
    """Verifica a igualdade de dois planos de entregas, considerando
    apenas os campos obrigatórios.
    """
    # Compara o conteúdo de todos os campos obrigatórios do plano de
    # entregas, exceto a lista de entregas
    assert all(
        plano_entregas_1[attribute] == plano_entregas_2[attribute]
        for attributes in FIELDS_PLANO_ENTREGAS["mandatory"]
        for attribute in attributes
        if attribute not in ("entregas")
    )

    # Compara o conteúdo de cada entrega, somente campos obrigatórios
    first_plan_by_entrega = {
        entrega["id_entrega"]: entrega for entrega in plano_entregas_1["entregas"]
    }
    second_plan_by_entrega = {
        entrega["id_entrega"]: entrega for entrega in plano_entregas_2["entregas"]
    }
    assert all(
        first_plan_by_entrega[id_entrega][attribute] == entrega[attribute]
        for attributes in FIELDS_ENTREGA["mandatory"]
        for attribute in attributes
        for id_entrega, entrega in second_plan_by_entrega.items()
    )


# Os testes usam muitas fixtures, então necessariamente precisam de
# muitos argumentos. Além disso, algumas fixtures não retornam um valor
# para ser usado no teste, mas mesmo assim são executadas quando estão
# presentes como um argumento da função.
# A linha abaixo desabilita os warnings do Pylint sobre isso.
# pylint: disable=too-many-arguments


def test_create_plano_entregas_completo(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um novo plano de entregas"""
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == http_status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert_equal_plano_entregas(response.json(), input_pe)


def test_update_plano_entregas(
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um novo plano de entregas e atualizar alguns campos.
    A fixture example_pe cria um novo Plano de Entregas na API.
    O teste altera um campo do PE e reenvia pra API (update).
    """

    input_pe["avaliacao"] = 3
    input_pe["data_avaliacao"] = "2023-08-15"
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == http_status.HTTP_200_OK
    assert response.json()["avaliacao"] == 3
    assert response.json()["data_avaliacao"] == "2023-08-15"

    # Consulta API para conferir se a alteração foi persistida
    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        headers=header_usr_1,
    )

    assert response.status_code == http_status.HTTP_200_OK
    assert response.json()["avaliacao"] == 3
    assert response.json()["data_avaliacao"] == "2023-08-15"


@pytest.mark.parametrize("omitted_fields", enumerate(FIELDS_ENTREGA["optional"]))
def test_create_plano_entregas_entrega_omit_optional_fields(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    omitted_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um novo plano de entregas omitindo campos opcionais"""

    offset, field_list = omitted_fields
    for field in field_list:
        for entrega in input_pe["entregas"]:
            if field in entrega:
                del entrega[field]

    input_pe["id_plano_entregas"] = str(557 + offset)
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == http_status.HTTP_201_CREATED
    assert_equal_plano_entregas(response.json(), input_pe)


@pytest.mark.parametrize("nulled_fields", enumerate(FIELDS_ENTREGA["optional"]))
def test_create_plano_entregas_entrega_null_optional_fields(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    nulled_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um novo plano de entregas com o valor null nos campos opcionais"""

    offset, field_list = nulled_fields
    for field in field_list:
        for entrega in input_pe["entregas"]:
            if field in entrega:
                entrega[field] = None

    input_pe["id_plano_entregas"] = str(557 + offset)
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == http_status.HTTP_201_CREATED
    assert_equal_plano_entregas(response.json(), input_pe)


@pytest.mark.parametrize(
    "missing_fields", enumerate(FIELDS_PLANO_ENTREGAS["mandatory"])
)
def test_create_plano_entregas_missing_mandatory_fields(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    missing_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entregas, faltando campos obrigatórios.
    Na atualização com PUT, ainda assim é necessário informar todos os
    campos obrigatórios, uma vez que o conteúdo será substituído.
    """
    offset, field_list = missing_fields
    for field in field_list:
        del input_pe[field]

    # para usar na URL, necessário existir caso tenha sido removido
    # como campo obrigatório
    id_plano_entregas = 1800 + offset
    if input_pe.get("id_plano_entregas", None):
        # Atualiza o id_plano_entrega somente se existir.
        # Se não existir, é porque foi removido como campo obrigatório.
        input_pe["id_plano_entregas"] = id_plano_entregas
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{id_plano_entregas}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_huge_plano_entregas(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Testa a criação de um plano de entregas com grande volume de dados."""

    def create_huge_entrega(id_entrega: int):
        new_entrega = input_pe["entregas"][0].copy()
        new_entrega["id_entrega"] = str(3 + id_entrega)
        new_entrega["nome_entrega"] = "x" * 300  # 300 caracteres
        new_entrega["nome_unidade_demandante"] = "x" * 300  # 300 caracteres
        new_entrega["nome_unidade_destinataria"] = "x" * 300  # 300 caracteres

        return new_entrega

    for id_entrega in range(200):
        input_pe["entregas"].append(create_huge_entrega(id_entrega))

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    # Compara o conteúdo do plano de entregas, somente campos obrigatórios
    assert response.status_code == http_status.HTTP_201_CREATED
    assert_equal_plano_entregas(response.json(), input_pe)

    # Compara o conteúdo de cada entrega, somente campos obrigatórios
    response_by_entrega = {
        entrega["id_entrega"]: entrega for entrega in response.json()["entregas"]
    }
    input_by_entrega = {entrega["id_entrega"]: entrega for entrega in input_pe["entregas"]}
    assert all(
        response_by_entrega[id_entrega][attribute] == entrega[attribute]
        for attributes in FIELDS_ENTREGA["mandatory"]
        for attribute in attributes
        for id_entrega, entrega in input_by_entrega.items()
    )


@pytest.mark.parametrize(
    "id_plano_entregas, nome_entrega, nome_unidade_demandante, nome_unidade_destinataria",
    [
        ("1", "x" * 301, "string", "string"),
        ("2", "string", "x" * 301, "string"),
        ("3", "string", "string", "x" * 301),
        ("4", "x" * 300, "x" * 300, "x" * 300),
    ],
)
def test_create_pe_exceed_string_max_size(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    id_plano_entregas: str,
    nome_entrega: str,  # 300 caracteres
    nome_unidade_demandante: str,  # 300 caracteres
    nome_unidade_destinataria: str,  # 300 caracteres
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Testa a criação de um plano de entregas excedendo o tamanho
    máximo de cada campo"""

    input_pe["id_plano_entregas"] = id_plano_entregas
    input_pe["entregas"][0]["nome_entrega"] = nome_entrega  # 300 caracteres
    input_pe["entregas"][0][
        "nome_unidade_demandante"
    ] = nome_unidade_demandante  # 300 caracteres
    input_pe["entregas"][0][
        "nome_unidade_destinataria"
    ] = nome_unidade_destinataria  # 300 caracteres

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if any(
        len(campo) > STR_MAX_SIZE
        for campo in (nome_entrega, nome_unidade_demandante, nome_unidade_destinataria)
    ):
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "String should have at most 300 characters"
        assert response.json().get("detail")[0]["msg"] == detail_message
    else:
        assert response.status_code == http_status.HTTP_201_CREATED


def test_create_pe_cod_plano_inconsistent(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entregas com código de plano divergente"""

    input_pe["id_plano_entregas"] = "110"
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/111",  # diferente de 110
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro id_plano_entregas na URL e no JSON devem ser iguais"
    assert response.json().get("detail", None) == detail_msg


def test_create_pe_cod_unidade_inconsistent(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entregas com código de unidade divergente"""
    original_input_pe = input_pe.copy()
    input_pe["cod_unidade_autorizadora"] = 999  # era 1
    response = client.put(
        f"/organizacao/SIAPE/{original_input_pe['cod_unidade_autorizadora']}"
        f"/plano_entregas/{original_input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro cod_unidade_autorizadora na URL e no JSON devem ser iguais"
    assert response.json().get("detail", None) == detail_msg


def test_get_plano_entregas(
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    user1_credentials: dict,
    header_usr_1: dict,
    input_pe,
    client: Client,
):
    """Tenta buscar um plano de entregas existente"""

    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        headers=header_usr_1,
    )
    assert response.status_code == http_status.HTTP_200_OK
    assert_equal_plano_entregas(response.json(), input_pe)


def test_get_pe_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    """Tenta buscar um plano de entregas inexistente"""

    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        "/plano_entregas/888888888",
        headers=header_usr_1,
    )
    assert response.status_code == http_status.HTTP_404_NOT_FOUND

    assert response.json().get("detail", None) == "Plano de entregas não encontrado"


@pytest.mark.parametrize(
    "id_plano_entregas, status, avaliacao, data_avaliacao",
    [
        ("78", 5, 2, "2023-06-11"),
        ("79", 5, 2, None), # falta data_avaliacao
        ("80", 5, None, "2023-06-11"), # falta avaliacao
        ("81", 5, None, None), # faltam ambos
        ("81", 2, None, None), # status não é 5
    ],
)
def test_create_pe_status_avaliado(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    status: int,
    avaliacao: int,
    data_avaliacao: str,
    id_plano_entregas: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entregas com datas de avaliação omitidas
    ou preenchidas, a depender do status.

    O status 5 só poderá ser usado se os campos “avaliacao” e “data_avaliacao”
    estiverem preenchidos.
    """

    input_pe["status"] = status
    input_pe["avaliacao"] = avaliacao
    input_pe["data_avaliacao"] = data_avaliacao
    input_pe["id_plano_entregas"] = id_plano_entregas

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{id_plano_entregas}",
        json=input_pe,
        headers=header_usr_1,
    )

    if status == 5 and not (avaliacao and data_avaliacao):
        assert response.status_code == 422
        detail_message = (
            "O status 5 só poderá ser usado se os campos avaliacao e "
            "data_avaliacao estiverem preenchidos."
        )
        assert_error_message(response, detail_message)
    else:
        assert response.status_code == http_status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_entregas, id_entrega_1, id_entrega_2",
    [
        ("90", "401", "402"),
        ("91", "403", "403"),  # <<<< IGUAIS
        ("92", "404", "404"),  # <<<< IGUAIS
        ("93", "405", "406"),
    ],
)
def test_create_pe_duplicate_entrega(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    id_plano_entregas: str,
    id_entrega_1: str,
    id_entrega_2: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entregas com entregas com id_entrega duplicados"""

    input_pe["id_plano_entregas"] = id_plano_entregas
    input_pe["entregas"][0]["id_entrega"] = id_entrega_1
    input_pe["entregas"][1]["id_entrega"] = id_entrega_2

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{id_plano_entregas}",
        json=input_pe,
        headers=header_usr_1,
    )
    if id_entrega_1 == id_entrega_2:
        assert response.status_code == 422
        detail_message = "Entregas devem possuir id_entrega diferentes"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == http_status.HTTP_201_CREATED


def test_create_pe_duplicate_id_plano(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entregas duplicado. O envio do mesmo
    plano de entregas pela segunda vez deve substituir o primeiro.
    """

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == http_status.HTTP_201_CREATED

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == http_status.HTTP_200_OK
    assert response.json().get("detail", None) is None
    assert_equal_plano_entregas(response.json(), input_pe)


def test_create_pe_same_id_plano_different_instituidora(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    user2_credentials: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    client: Client,
):
    """Tenta criar um plano de entregas duplicado. O envio do mesmo
    plano de entregas pela segunda vez deve substituir o primeiro.
    """

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == http_status.HTTP_201_CREATED

    input_pe["cod_unidade_instituidora"] = user2_credentials["cod_unidade_autorizadora"]
    response = client.put(
        f"/organizacao/SIAPE/{user2_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_2,
    )
    assert response.status_code == http_status.HTTP_201_CREATED


@pytest.mark.parametrize("cod_unidade_executora", [99, 0, -1])
def test_create_invalid_cod_unidade(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    cod_unidade_executora: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar uma entrega com código de unidade inválido.
    Por ora não será feita validação no sistema, e sim apenas uma
    verificação de sanidade.
    """
    input_pe["cod_unidade_executora"] = cod_unidade_executora

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if cod_unidade_executora > 0:
        assert response.status_code == http_status.HTTP_201_CREATED
    else:
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "cod_unidade_executora inválido"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


@pytest.mark.parametrize(
    "id_plano_entregas, meta_entrega, tipo_meta",
    [
        ("555", 10, "unidade"),
        ("556", 100, "percentual"),
        ("557", 1, "percentual"),
        ("558", -10, "unidade"),
        ("559", 200, "percentual"),
    ],
)
def test_create_entrega_invalid_percent(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    id_plano_entregas: str,
    meta_entrega: int,
    tipo_meta: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um Plano de Entregas com entrega com percentuais inválidos"""
    input_pe["id_plano_entregas"] = id_plano_entregas
    input_pe["entregas"][1]["meta_entrega"] = meta_entrega
    input_pe["entregas"][1]["tipo_meta"] = tipo_meta

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if tipo_meta == "percentual" and (meta_entrega < 0 or meta_entrega > 100):
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Valor meta_entrega deve estar entre 0 e 100 "
            "quando tipo_entrega for percentual."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    elif tipo_meta == "unidade" and (meta_entrega < 0):
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Valor meta_entrega deve ser positivo quando tipo_entrega for unidade."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == http_status.HTTP_201_CREATED


@pytest.mark.parametrize("tipo_meta", ["unidade", "percentual", "invalid"])
def test_create_entrega_invalid_tipo_meta(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    tipo_meta: str,
    client: Client,
):
    """Tenta criar um Plano de Entregas com tipo de meta inválido"""
    input_pe["entregas"][0]["tipo_meta"] = tipo_meta

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if tipo_meta in ("unidade", "percentual"):
        assert response.status_code == http_status.HTTP_201_CREATED
    else:
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Tipo de meta inválido; permitido: 'unidade', 'percentual'"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


@pytest.mark.parametrize("avaliacao", [-1, 0, 1, 6])
def test_create_pe_invalid_avaliacao(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    avaliacao: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um Plano de Entregas com nota de avaliação inválida"""

    input_pe["avaliacao"] = avaliacao
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if avaliacao in range(1, 6):
        assert response.status_code == http_status.HTTP_201_CREATED
    else:
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Nota de avaliação inválida; permitido: 1, 2, 3, 4, 5"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
