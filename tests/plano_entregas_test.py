"""
Testes relacionados ao Plano de Entregas da Unidade
"""

from datetime import date

from httpx import Client
from fastapi import status

import pytest

from util import over_a_year

# grupos de campos opcionais e obrigatórios a testar

fields_plano_entregas = {
    "optional": (
        ["avaliacao"],
        ["data_avaliacao"],
    ),
    "mandatory": (
        ["origem_unidade"],
        ["cod_unidade_autorizadora"],
        ["cod_unidade_instituidora"],
        ["cod_unidade_executora"],
        ["id_plano_entrega"],
        ["status"],
        ["data_inicio"],
        ["data_termino"],
        ["entregas"],
    ),
}

fields_entrega = {
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
        for attributes in fields_plano_entregas["mandatory"]
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
        for attributes in fields_entrega["mandatory"]
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
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert_equal_plano_entregas(response.json(), input_pe)


def test_create_plano_entregas_unidade_nao_permitida(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    header_usr_2: dict,
    client: Client,
):
    """Tenta criar um novo Plano de Entregas em uma organização na qual
    ele não está autorizado.
    """
    response = client.put(
        "/organizacao/SIAPE/3"  # só está autorizado na organização 2
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        response.json().get("detail", None)
        == "Usuário não tem permissão na cod_unidade_instituidora informada"
    )


def test_create_plano_entregas_outra_unidade_admin(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    header_admin: dict,
    admin_credentials: dict,
    client: Client,
):
    """Tenta, como administrador, criar um novo Plano de Entregas em uma
    organização diferente da sua própria organização.
    """
    input_pe["cod_unidade_autorizadora"] = 3  # unidade diferente

    response = client.get(
        f"/user/{admin_credentials['username']}",
        headers=header_admin,
    )

    # Verifica se o usuário é admin e se está em outra unidade
    assert response.status_code == status.HTTP_200_OK
    admin_data = response.json()
    assert (
        admin_data.get("cod_unidade_autorizadora", None)
        != input_pe["cod_unidade_autorizadora"]
    )
    assert admin_data.get("is_admin", None) is True

    response = client.put(
        f"/organizacao/SIAPE/{input_pe['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_admin,
    )

    assert response.status_code == status.HTTP_201_CREATED
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
    A fixture example_pe cria um novo Plano de Entrega na API.
    O teste altera um campo do PE e reenvia pra API (update).
    """

    input_pe["avaliacao"] = 3
    input_pe["data_avaliacao"] = "2023-08-15"
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["avaliacao"] == 3
    assert response.json()["data_avaliacao"] == "2023-08-15"

    # Consulta API para conferir se a alteração foi persistida
    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["avaliacao"] == 3
    assert response.json()["data_avaliacao"] == "2023-08-15"


@pytest.mark.parametrize("omitted_fields", enumerate(fields_entrega["optional"]))
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

    input_pe["id_plano_entrega"] = 557 + offset
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert_equal_plano_entregas(response.json(), input_pe)


@pytest.mark.parametrize("nulled_fields", enumerate(fields_entrega["optional"]))
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

    input_pe["id_plano_entrega"] = 557 + offset
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert_equal_plano_entregas(response.json(), input_pe)


@pytest.mark.parametrize(
    "missing_fields", enumerate(fields_plano_entregas["mandatory"])
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
    id_plano_entrega = 1800 + offset
    if input_pe.get("id_plano_entrega", None):
        # Atualiza o id_plano_entrega somente se existir.
        # Se não existir, é porque foi removido como campo obrigatório.
        input_pe["id_plano_entrega"] = id_plano_entrega
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{id_plano_entrega}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


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
        new_entrega["id_entrega"] = 3 + id_entrega
        new_entrega["nome_entrega"] = "x" * 300  # 300 caracteres
        new_entrega["nome_unidade_demandante"] = "x" * 300  # 300 caracteres
        new_entrega["nome_unidade_destinataria"] = "x" * 300  # 300 caracteres

        return new_entrega

    for id_entrega in range(200):
        input_pe["entregas"].append(create_huge_entrega(id_entrega))

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    # Compara o conteúdo do plano de entregas, somente campos obrigatórios
    assert response.status_code == status.HTTP_201_CREATED
    assert_equal_plano_entregas(response.json(), input_pe)

    # Compara o conteúdo de cada entrega, somente campos obrigatórios
    response_by_entrega = {
        id_entrega: entrega for entrega in response.json()["entregas"]
    }
    input_by_entrega = {id_entrega: entrega for entrega in input_pe["entregas"]}
    assert all(
        response_by_entrega[id_entrega][attribute] == entrega[attribute]
        for attributes in fields_entrega["mandatory"]
        for attribute in attributes
        for id_entrega, entrega in input_by_entrega.items()
    )


@pytest.mark.parametrize(
    "id_plano_entrega, nome_entrega, nome_unidade_demandante, nome_unidade_destinataria",
    [
        (1, "x" * 301, "string", "string"),
        (2, "string", "x" * 301, "string"),
        (3, "string", "string", "x" * 301),
        (4, "x" * 300, "x" * 300, "x" * 300),
    ],
)
def test_create_pe_exceed_string_max_size(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    id_plano_entrega: int,
    nome_entrega: str,  # 300 caracteres
    nome_unidade_demandante: str,  # 300 caracteres
    nome_unidade_destinataria: str,  # 300 caracteres
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
    str_max_size: int = 300,
):
    """Testa a criação de um plano de entregas excedendo o tamanho
    máximo de cada campo"""

    input_pe["id_plano_entrega"] = id_plano_entrega
    input_pe["entregas"][0]["nome_entrega"] = nome_entrega  # 300 caracteres
    input_pe["entregas"][0][
        "nome_unidade_demandante"
    ] = nome_unidade_demandante  # 300 caracteres
    input_pe["entregas"][0][
        "nome_unidade_destinataria"
    ] = nome_unidade_destinataria  # 300 caracteres

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if any(
        len(campo) > str_max_size
        for campo in (nome_entrega, nome_unidade_demandante, nome_unidade_destinataria)
    ):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "String should have at most 300 characters"
        assert response.json().get("detail")[0]["msg"] == detail_message
    else:
        assert response.status_code == status.HTTP_201_CREATED


# TODO: verbo PATCH poderá ser implementado em versão futura.
#
# @pytest.mark.parametrize("missing_fields", fields_plano_entregas["mandatory"])
# def test_patch_plano_entregas_inexistente(
#     truncate_pe,
#     input_pe: dict,
#     missing_fields: list,
#     user1_credentials: dict,
#     header_usr_1: dict,
#     client: Client,
# ):
#     """Tenta atualizar um plano de entrega com PATCH, faltando campos
#     obrigatórios.

#     Com o verbo PATCH, os campos omitidos são interpretados como sem
#     alteração. Por isso, é permitido omitir os campos obrigatórios.
#     """
#     example_pe = input_pe.copy()
#     for field in missing_fields:
#         del input_pe[field]

#     input_pe["id_plano_entrega_unidade"] = 999  # precisa ser um plano inexistente
#     response = client.patch(
#         f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
#         f"/plano_entregas/{example_pe['id_plano_entrega_unidade']}",
#         json=input_pe,
#         headers=header_usr_1,
#     )
#     assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "id_plano_entrega, cod_unidade_executora, " "data_inicio, data_termino, " "status",
    [
        ("1", 99, "2023-01-01", "2023-06-30", 4),  # igual ao exemplo
        ("2", 99, "2024-01-01", "2024-06-30", 4),  # sem sobreposição
        ("3", 99, "2022-12-01", "2023-01-31", 4),  # sobreposição no início
        ("4", 99, "2023-12-01", "2024-01-31", 4),  # sobreposição no fim
        ("5", 99, "2023-02-01", "2023-05-31", 4),  # contido no período
        ("6", 99, "2022-12-01", "2024-01-31", 4),  # contém o período
        ("7", 100, "2023-02-01", "2023-05-31", 4),  # outra unidade
        # sobreposição porém um é cancelado
        ("8", 99, "2022-12-01", "2023-01-31", 1),
    ],
)
def test_create_plano_entregas_overlapping_date_interval(
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    id_plano_entrega: str,
    cod_unidade_executora: int,
    data_inicio: str,
    data_termino: str,
    status: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entregas com sobreposição de intervalo de
    data na mesma unidade.

    O Plano de Entregas original é criado e então é testada a criação de
    cada novo Plano de Entregas, com sobreposição ou não das datas,
    conforme especificado nos parâmetros de teste.
    """
    original_pe = input_pe.copy()
    input_pe2 = original_pe.copy()
    input_pe2["id_plano_entrega"] = "2"
    input_pe2["data_inicio"] = "2023-07-01"
    input_pe2["data_termino"] = "2023-12-31"
    for entrega in input_pe2["entregas"]:
        entrega["data_entrega"] = "2023-12-31"
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe2['id_plano_entrega']}",
        json=input_pe2,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED

    input_pe["id_plano_entrega"] = id_plano_entrega
    input_pe["cod_unidade_executora"] = cod_unidade_executora
    input_pe["data_inicio"] = data_inicio
    input_pe["data_termino"] = data_termino
    input_pe["status"] = status
    for entrega in input_pe["entregas"]:
        entrega["data_entrega"] = data_termino
    del input_pe["avaliacao"]
    del input_pe["data_avaliacao"]
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )
    if (
        # se algum dos planos estiver cancelado, não há problema em haver
        # sobreposição
        input_pe["status"] == 1
        # se são unidades diferentes, não há problema em haver sobreposição
        or input_pe["cod_unidade_executora"] != original_pe["cod_unidade_executora"]
    ):
        # um dos planos está cancelado, deve ser criado
        assert response.status_code == status.HTTP_201_CREATED
        assert_equal_plano_entregas(response.json(), input_pe)
    else:
        if any(
            (
                date.fromisoformat(input_pe["data_inicio"])
                < date.fromisoformat(existing_pe["data_termino"])
            )
            and (
                date.fromisoformat(input_pe["data_termino"])
                > date.fromisoformat(existing_pe["data_inicio"])
            )
            for existing_pe in (original_pe, input_pe2)
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "Já existe um plano de entregas para esta "
                "cod_unidade_executora no período informado."
            )
            assert response.json().get("detail", None) == detail_msg
        else:
            # não há sobreposição de datas
            assert response.status_code == status.HTTP_201_CREATED
            assert_equal_plano_entregas(response.json(), input_pe)


@pytest.mark.parametrize(
    "data_inicio, data_termino",
    [
        ("2023-01-01", "2023-06-30"),  # igual ao exemplo
        ("2023-01-01", "2024-01-01"),  # um ano
        ("2023-01-01", "2024-01-02"),  # mais que um ano
    ],
)
def test_create_plano_entregas_date_interval_over_a_year(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    data_inicio: str,
    data_termino: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Plano de Entregas não pode ter vigência superior a um ano."""
    input_pe["data_inicio"] = data_inicio
    input_pe["data_termino"] = data_termino

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if (
        over_a_year(
            date.fromisoformat(data_termino),
            date.fromisoformat(data_inicio),
        )
        == 1
    ):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Plano de entregas não pode abranger período maior que 1 ano."
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED
        assert_equal_plano_entregas(response.json(), input_pe)


def test_create_pe_cod_plano_inconsistent(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entrega com código de plano divergente"""

    input_pe["id_plano_entrega"] = "110"
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/111",  # diferente de 110
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro cod_unidade_autorizadora na URL e no JSON devem ser iguais"
    assert response.json().get("detail", None) == detail_msg


def test_create_pe_cod_unidade_inconsistent(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entrega com código de unidade divergente"""
    original_input_pe = input_pe.copy()
    input_pe["cod_unidade_autorizadora"] = 999  # era 1
    response = client.put(
        f"/organizacao/SIAPE/{original_input_pe['cod_unidade_autorizadora']}"
        f"/plano_entregas/{original_input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
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
    """Tenta buscar um plano de entrega existente"""

    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_entregas(response.json(), input_pe)


def test_get_pe_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    """Tenta buscar um plano de entrega inexistente"""

    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        "/plano_entregas/888888888",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert response.json().get("detail", None) == "Plano de entregas não encontrado"


def test_get_plano_entregas_different_unit(
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    header_usr_2: dict,
    input_pe,
    client: Client,
):
    """Tenta buscar um plano de entrega existente em uma unidade diferente,
    à qual o usuário não tem acesso."""

    response = client.get(
        f"/organizacao/SIAPE/3"  # Sem autorização nesta unidade
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        headers=header_usr_2,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_plano_entregas_different_unit_admin(
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    header_admin: dict,
    input_pe,
    client: Client,
):
    """Tenta buscar um plano de entrega existente em uma unidade diferente, mas
    com um usuário com permissão de admin."""

    response = client.get(
        f"/organizacao/SIAPE/3"  # Unidade diferente
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        headers=header_admin,
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "data_inicio, data_termino",
    [
        ("2020-06-04", "2020-04-01"),
    ],
)
def test_create_pe_invalid_period(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    data_inicio: str,
    data_termino: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entrega com datas trocadas"""

    input_pe["data_inicio"] = data_inicio
    input_pe["data_termino"] = data_termino

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )
    if data_inicio > data_termino:
        assert response.status_code == 422
        detail_message = "data_termino deve ser maior ou igual que data_inicio."
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_entrega, data_inicio, data_termino, data_entrega",
    [
        ("91", "2023-08-01", "2023-09-01", "2023-08-08"),
        ("92", "2023-08-01", "2023-09-01", "2023-07-01"),
        ("93", "2023-08-01", "2023-09-01", "2023-10-01"),
    ],
)
def test_create_data_entrega_out_of_bounds(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    id_plano_entrega: str,
    data_inicio: str,
    data_termino: str,
    data_entrega: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar uma entrega com data de entrega dentro e fora do
    intervalo do plano de entrega. Segundo as regras de negócio, essa
    data pode estar em qualquer ponto no tempo, dentro ou fora do período
    do plano_entregas.
    """
    input_pe["id_plano_entrega"] = id_plano_entrega
    input_pe["data_inicio"] = data_inicio
    input_pe["data_termino"] = data_termino
    for entrega in input_pe["entregas"]:
        entrega["data_entrega"] = data_entrega

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{id_plano_entrega}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_entrega, data_inicio, data_avaliacao",
    [
        ("77", "2020-06-04", "2020-04-01"),
        ("78", "2020-06-04", "2020-06-11"),
    ],
)
def test_create_pe_invalid_data_avaliacao(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    data_inicio: str,
    data_avaliacao: str,
    id_plano_entrega: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entrega com datas de avaliação inferior a data de inicio do Plano"""

    input_pe["data_inicio"] = data_inicio
    input_pe["data_avaliacao"] = data_avaliacao
    input_pe["id_plano_entrega"] = id_plano_entrega

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{id_plano_entrega}",
        json=input_pe,
        headers=header_usr_1,
    )

    if data_avaliacao < data_inicio:
        assert response.status_code == 422
        detail_message = (
            "Data de avaliação do Plano de Entrega deve ser maior ou igual"
            " que a Data de início do Plano de Entrega."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_entrega, id_entrega_1, id_entrega_2",
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
    id_plano_entrega: str,
    id_entrega_1: str,
    id_entrega_2: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de entrega com entregas com id_entrega duplicados"""

    input_pe["id_plano_entrega"] = id_plano_entrega
    input_pe["entregas"][0]["id_entrega"] = id_entrega_1
    input_pe["entregas"][1]["id_entrega"] = id_entrega_2

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{id_plano_entrega}",
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
        assert response.status_code == status.HTTP_201_CREATED


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
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
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
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED

    input_pe["cod_unidade_instituidora"] = user2_credentials["cod_unidade_autorizadora"]
    response = client.put(
        f"/organizacao/SIAPE/{user2_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_2,
    )
    assert response.status_code == status.HTTP_201_CREATED


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
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if cod_unidade_executora > 0:
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "cod_unidade_executora inválido"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


@pytest.mark.parametrize(
    "id_plano_entrega, meta_entrega, tipo_meta",
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
    id_plano_entrega: str,
    meta_entrega: int,
    tipo_meta: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um Plano de Entrega com entrega com percentuais inválidos"""
    input_pe["id_plano_entrega"] = id_plano_entrega
    input_pe["entregas"][1]["meta_entrega"] = meta_entrega
    input_pe["entregas"][1]["tipo_meta"] = tipo_meta

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if tipo_meta == "percentual" and (meta_entrega < 0 or meta_entrega > 100):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Valor meta_entrega deve estar entre 0 e 100 "
            "quando tipo_entrega for percentual."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    elif tipo_meta == "unidade" and (meta_entrega < 0):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Valor meta_entrega deve ser positivo quando tipo_entrega for unidade."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("tipo_meta", [0, 1, 2, 3, 10])
def test_create_entrega_invalid_tipo_meta(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    tipo_meta: int,
    client: Client,
):
    """Tenta criar um Plano de Entrega com tipo de meta inválido"""
    input_pe["entregas"][0]["tipo_meta"] = tipo_meta

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if tipo_meta in (1, 2):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Tipo de meta inválido; permitido: 1, 2"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


@pytest.mark.parametrize("avaliacao_plano_entregas", [-1, 0, 1, 6])
def test_create_pe_invalid_avaliacao(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    avaliacao_plano_entregas: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um Plano de Entrega com nota de avaliação inválida"""

    input_pe["avaliacao_plano_entregas"] = avaliacao_plano_entregas
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if avaliacao_plano_entregas in range(1, 6):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Nota de avaliação inválida; permitido: 1, 2, 3, 4, 5"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
