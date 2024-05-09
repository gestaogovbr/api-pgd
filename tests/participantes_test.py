"""
Testes relacionados aos status de participantes.
"""
from httpx import Client

from fastapi import status

import pytest

# Relação de campos obrigatórios para testar sua ausência:
fields_participantes = {
    "optional": tuple(), # nenhum campo é opcional
    "mandatory": (
        ["cod_SIAPE_instituidora"],
        ["cod_SIAPE_lotacao"],
        ["cpf_participante"],
        ["participante"],
        ["modalidade_execucao"],
        ["data_assinatura_tcr"],
    ),
}


# Helper functions


def remove_null_optional_fields(data: dict) -> dict:
    """Remove fields that are None from the data."""
    if not isinstance(data, dict):
        print(f"data: {data}")
        print(f"type: {type(data)}")
        raise ValueError("Data must be a dict")
    for fields in fields_participantes["optional"]:
        for field in fields:
            if field in data and data[field] is None:
                del data[field]
    return data


def assert_equal_lista_status_participante(
    status_participante_1: list[dict], status_participante_2: list[dict]
):
    """Verifica a igualdade de duas listas de status do participante, considerando
    apenas os campos obrigatórios.
    """

    status_participante_1 = sorted([
        remove_null_optional_fields(status_participante)
        for status_participante in status_participante_1
    ])
    status_participante_2 = sorted([
        remove_null_optional_fields(status_participante)
        for status_participante in status_participante_2
    ])
    assert status_participante_1 == status_participante_2


# Os testes usam muitas fixtures, então necessariamente precisam de
# muitos argumentos. Além disso, algumas fixtures não retornam um valor
# para ser usado no teste, mas mesmo assim são executadas quando estão
# presentes como um argumento da função.
# A linha abaixo desabilita os warnings do Pylint sobre isso.
# pylint: disable=too-many-arguments


def test_put_participante(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Testa a submissão de um participante a partir do template"""
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_lotacao']}"
        f"/participante/{input_part['cpf_participante']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert_equal_lista_status_participante(response.json(), input_part)


def test_put_participante_unidade_nao_permitida(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    header_usr_2: dict,
    client: Client,
):
    """
    Testa a submissão de um participante em outra unidade instituidora
    (user não é superuser)
    """
    response = client.put(
        f"/organizacao/3/participante/{input_part['cpf_participante']}",
        json=input_part,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    detail_msg = "Usuário não tem permissão na cod_SIAPE_instituidora informada"
    assert response.json().get("detail", None) == detail_msg


def test_put_participante_outra_unidade_admin(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    header_admin: dict,
    admin_credentials: dict,
    client: Client,
):
    """Testa, usando usuário admin, a submissão de um participante em outra
    unidade instituidora
    """
    input_part["cod_SIAPE_instituidora"] = 3  # unidade diferente

    response = client.get(
        f"/user/{admin_credentials['username']}",
        headers=header_admin,
    )

    # Verifica se o usuário é admin e se está em outra unidade
    assert response.status_code == status.HTTP_200_OK
    admin_data = response.json()
    assert (
        admin_data.get("cod_SIAPE_instituidora", None)
        != input_part["cod_SIAPE_instituidora"]
    )
    assert admin_data.get("is_admin", None) is True

    response = client.put(
        f"/organizacao/3/participante/{input_part['cpf_participante']}",
        json=input_part,
        headers=header_admin,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert response.json() == input_part


@pytest.mark.parametrize(
    "codigos_SIAPE_instituidora",
    [
        (1, 1),  # mesma unidade
        (1, 2),  # unidades diferentes
    ],
)
def test_put_duplicate_participante(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    codigos_SIAPE_instituidora: tuple[int, int],
    user1_credentials: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    client: Client,
):
    """Testa o envio de um mesmo participante mais de uma vez. Podendo
    ser em unidades diferentes (por exemplo, quando o participante altera
    a sua lotação) ou na mesma unidade (envio de um novo status para o
    mesmo participante, na mesma unidade). Em todos os casos tem que se
    manter o(s) registro(s) anterior(es) concomitantemente.
    """
    input_part["cod_SIAPE_instituidora"] = codigos_SIAPE_instituidora[0]
    response = client.put(
        f"/organizacao/{codigos_SIAPE_instituidora[0]}"
        f"/participante/{input_part['cpf_participante']}",
        json={"lista_status": [input_part]},
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert response.json() == input_part

    if codigos_SIAPE_instituidora[1] == user1_credentials["cod_SIAPE_instituidora"]:
        header_usr = header_usr_1
    else:
        header_usr = header_usr_2
    input_part["cod_SIAPE_instituidora"] = codigos_SIAPE_instituidora[1]
    response = client.put(
        f"/organizacao/{codigos_SIAPE_instituidora[1]}"
        f"/participante/{input_part['cpf_participante']}",
        json=input_part,
        headers=header_usr,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert response.json() == input_part


def test_create_participante_inconsistent(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta submeter participante inconsistente (URL difere do JSON)"""
    novo_cpf_participante = "82893311776"
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{novo_cpf_participante}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro cpf_participante na URL e no JSON devem ser iguais"
    assert response.json().get("detail", None) == detail_msg


# @pytest.mark.parametrize("omitted_fields", enumerate(fields_participantes["optional"]))
# def test_put_participante_omit_optional_fields(
#     truncate_participantes,  # pylint: disable=unused-argument
#     input_part: dict,
#     omitted_fields: list,
#     user1_credentials: dict,
#     header_usr_1: dict,
#     client: Client,
# ):
#     """Tenta criar uma nova lista de status de participante omitindo
#     campos opcionais.
#     """
#     partial_input_part = input_part.copy()
#     cpf_participante = partial_input_part["cpf_participante"]
#     _, field_list = omitted_fields
#     for field in field_list:
#         del partial_input_part[field]

#     response = client.put(
#         f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
#         f"/participante/{cpf_participante}",
#         json={"lista_status": [partial_input_part]},
#         headers=header_usr_1,
#     )
#     assert response.status_code == status.HTTP_201_CREATED
#     assert any(
#         all(
#             response_part[attribute] == partial_input_part[attribute]
#             for attributes in fields_participantes["mandatory"]
#             for attribute in attributes
#         )
#         for response_part in response.json()["lista_status"]
#     )


@pytest.mark.parametrize("missing_fields", enumerate(fields_participantes["mandatory"]))
def test_put_participante_missing_mandatory_fields(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    missing_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta submeter participantes faltando campos obrigatórios"""
    cpf_participante = input_part["cpf_participante"]
    offset, field_list = missing_fields
    for field in field_list:
        del input_part[field]

    input_part[
        "cpf_participante"
    ] = f"{1800 + offset}"  # precisa ser um novo participante
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{cpf_participante}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_participante(
    truncate_participantes,  # pylint: disable=unused-argument
    example_part,  # pylint: disable=unused-argument
    header_usr_1: dict,
    input_part: dict,
    client: Client,
):
    """Tenta requisitar um participante pela matricula_siape."""
    response = client.get(
        f"/organizacao/{input_part['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['cpf_participante']}",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert_equal_lista_status_participante(
        [response.json()], [input_part]
    )


def test_get_participante_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    """Tenta consultar um participante que não existe na base de dados."""
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/participante/82893311776",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        response.json().get("detail", None) == "Status de Participante não encontrado"
    )


def test_get_participante_different_unit(
    truncate_participantes,  # pylint: disable=unused-argument
    example_part_unidade_3,  # pylint: disable=unused-argument
    input_part: dict,
    header_usr_2: dict,
    client: Client,
):
    """
    Testa ler um participante em outra unidade instituidora
    (user não é superuser)
    """

    input_part["cod_SIAPE_instituidora"] = 3

    response = client.get(
        f"/organizacao/{input_part['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['cpf_participante']}",
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    detail_msg = "Usuário não tem permissão na cod_SIAPE_instituidora informada"
    assert response.json().get("detail", None) == detail_msg


def test_get_participante_different_unit_admin(
    truncate_participantes,  # pylint: disable=unused-argument
    example_part_unidade_3,  # pylint: disable=unused-argument
    header_admin: dict,
    input_part: dict,
    client: Client,
):
    """Tenta requisitar um participante pela matricula_siape."""

    input_part["cod_SIAPE_instituidora"] = 3

    response = client.get(
        f"/organizacao/{input_part['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['cpf_participante']}",
        headers=header_admin,
    )
    assert response.status_code == status.HTTP_200_OK
    assert_equal_lista_status_participante(
        [response.json()], [input_part]
    )


@pytest.mark.parametrize(
    "matricula_siape",
    [
        ("12345678"),
        ("0000000"),
        ("9999999"),
        ("123456"),
        (""),
    ],
)
# def test_put_participante_invalid_matricula_siape(
#     truncate_participantes,  # pylint: disable=unused-argument
#     input_part: dict,
#     matricula_siape: str,
#     user1_credentials: dict,
#     header_usr_1: dict,
#     client: Client,
# ):
#     """Tenta submeter um participante com matricula siape inválida"""

#     input_part["matricula_siape"] = matricula_siape

#     response = client.put(
#         f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
#         f"/participante/{input_part['cpf_participante']}",
#         json={"lista_status": [input_part]},
#         headers=header_usr_1,
#     )
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     detail_messages = [
#         "Matricula SIAPE Inválida.",
#         "Matrícula SIAPE deve ter 7 dígitos.",
#     ]
#     assert any(
#         f"Value error, {message}" in error["msg"]
#         for message in detail_messages
#         for error in response.json().get("detail")
#     )


@pytest.mark.parametrize(
    "cpf_participante",
    [
        ("11111111111"),
        ("22222222222"),
        ("33333333333"),
        ("44444444444"),
        ("04811556435"),
        ("444444444"),
        ("4811556437"),
    ],
)
def test_put_participante_invalid_cpf(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    cpf_participante: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta submeter um participante com cpf inválido"""
    input_part["cpf_participante"] = cpf_participante

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['cpf_participante']}",
        json={"lista_status": [input_part]},
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_messages = [
        "Dígitos verificadores do CPF inválidos.",
        "CPF inválido.",
        "CPF precisa ter 11 dígitos.",
        "CPF deve conter apenas dígitos.",
    ]
    assert any(
        f"Value error, {message}" in error["msg"]
        for message in detail_messages
        for error in response.json().get("detail")
    )


@pytest.mark.parametrize(
    "participante_ativo_inativo_pgd",
    [
        (3),
        (-1),
    ],
)
def test_put_part_invalid_ativo(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    participante_ativo_inativo_pgd: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um participante com flag participante_ativo_inativo_pgd
    com valor inválido."""
    input_part["participante_ativo_inativo_pgd"] = participante_ativo_inativo_pgd
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['cpf_participante']}",
        json={"lista_status": [input_part]},
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_messages = (
        "Valor do campo 'participante_ativo_inativo_pgd' inválida; permitido: 0, 1"
    )
    assert any(
        f"Value error, {message}" in error["msg"]
        for message in detail_messages
        for error in response.json().get("detail")
    )


@pytest.mark.parametrize("modalidade_execucao", [(0), (-1), (5)])
def test_put_part_invalid_modalidade_execucao(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    modalidade_execucao: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta submeter um participante com modalidade de execução inválida"""
    input_part["modalidade_execucao"] = modalidade_execucao
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['cpf_participante']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_messages = "Modalidade de execução inválida; permitido: 1, 2, 3, 4"
    assert any(
        f"Value error, {message}" in error["msg"]
        for message in detail_messages
        for error in response.json().get("detail")
    )


# @pytest.mark.parametrize(
#     "jornada_trabalho_semanal",
#     [
#         (-2),
#         (0),
#     ],
# )
# def test_put_part_invalid_jornada_trabalho_semanal(
#     truncate_participantes,  # pylint: disable=unused-argument
#     input_part: dict,
#     jornada_trabalho_semanal: int,
#     user1_credentials: dict,
#     header_usr_1: dict,
#     client: Client,
# ):
#     """Tenta submeter um participante com jornada de trabalho semanal inválida"""
#     input_part["jornada_trabalho_semanal"] = jornada_trabalho_semanal
#     response = client.put(
#         f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
#         f"/participante/{input_part['cpf_participante']}",
#         json={"lista_status": [input_part]},
#         headers=header_usr_1,
#     )

#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     detail_messages = "Jornada de trabalho semanal deve ser maior que zero"
#     assert any(
#         f"Value error, {message}" in error["msg"]
#         for message in detail_messages
#         for error in response.json().get("detail")
#     )
