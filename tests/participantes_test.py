"""
Testes relacionados aos status de participantes
"""
import itertools

from httpx import Client

from fastapi import status

import pytest

fields_participantes = (
    ["participante_ativo_inativo_pgd"],
    ["matricula_siape"],
    ["cpf_participante"],
    ["modalidade_execucao"],
    ["jornada_trabalho_semanal"],
)


def test_put_participante(
    input_part: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    client: Client,
):
    """Testa a submissão de um participante a partir do template"""
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/participante/123456",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) == None
    assert response.json() == input_part


def test_put_duplicate_participante(
    input_part: dict,
    user1_credentials: dict,
    user2_credentials: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    truncate_participantes,
    client: Client,
):
    """Testa a submissão de um participante duplicado
    TODO: Verificar regra negocial"""
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/participante/123456",
        json=input_part,
        headers=header_usr_1,
    )
    response = client.put(
        f"/organizacao/{user2_credentials['cod_SIAPE_instituidora']}"
        "/participante/123456",
        json=input_part,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) == None
    assert response.json() == input_part


def test_create_participante_inconsistent(
    input_part: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    client: Client,
):
    """Tenta submeter participante inconsistente (URL difere do JSON)"""
    input_part["matricula_siape"] = 678910
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/123456",
        json=input_part,
        headers=header_usr_1,  # diferente de 678910
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = (
        "Parâmetro matricula_siape na URL e no JSON devem ser iguais"
    )
    assert response.json().get("detail", None) == detail_msg



@pytest.mark.parametrize("missing_fields", enumerate(fields_participantes))
def test_put_participante_missing_mandatory_fields(
    input_part: dict,
    missing_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    client: Client,
):
    """Tenta submeter participantes faltando campos obrigatórios"""
    offset, field_list = missing_fields
    for field in field_list:
        del input_part[field]

    input_part["matricula_siape"] = 1800 + offset  # precisa ser um novo participante
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_participante(
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    example_part,
    client: Client,
):
    """Tenta requisitar um participante pela matricula_siape.
    """
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/participante/123456",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_get_participante_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/participante/888888888",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail", None) == "Participante não encontrado"


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
def test_put_participante_invalid_matricula_siape(
    input_part: dict,
    matricula_siape: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    client: Client,
):
    """Tenta submeter um participante com matricula siape inválida"""

    input_part["matricula_siape"] = matricula_siape

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = [
        "Matricula SIAPE Inválida.",
        "Matrícula SIAPE deve ter 7 dígitos.",
    ]
    assert response.json().get("detail")[0]["msg"] in detail_msg


@pytest.mark.parametrize(
    "cpf",
    [
        ("11111111111"),
        ("22222222222"),
        ("33333333333"),
        ("44444444444"),
        ("04811556435"),
        ("444-444-444.44"),
        ("-44444444444"),
        ("444444444"),
        ("-444 4444444"),
        ("4811556437"),
        ("048115564-37"),
        ("04811556437     "),
        ("    04811556437     "),
        (""),
    ],
)
def test_put_participante_invalid_cpf(
    input_part: dict,
    cpf: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    client: Client,
):
    """Tenta submeter um participante com cpf inválido"""
    input_part["cpf"] = cpf

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = [
        "Dígitos verificadores do CPF inválidos.",
        "CPF inválido.",
        "CPF precisa ter 11 dígitos.",
        "CPF deve conter apenas dígitos.",
    ]
    assert response.json().get("detail")[0]["msg"] in detail_msg


@pytest.mark.parametrize(
    "participante_ativo_inativo_pgd",
    [
        (3),
        (-1),
    ],
)
def test_put_part_invalid_ativo(
    input_part: dict,
    participante_ativo_inativo_pgd: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    client: Client,
):
    """Tenta criar um participante com flag participante_ativo_inativo_pgd
    com valor inválido."""
    input_part["participante_ativo_inativo_pgd"] = participante_ativo_inativo_pgd
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = (
        "Valor do campo 'participante_ativo_inativo_pgd' inválida; permitido: 0, 1"
    )
    # detail_msg = "value is not a valid enumeration member; permitted: 0,1"
    assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize("modalidade_execucao", [(0), (-1), (5)])
def test_put_part_invalid_modalidade_execucao(
    input_part: dict,
    modalidade_execucao: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    client: Client,
):
    """Tenta submeter um participante com modalidade de execução inválida"""
    input_part["modalidade_execucao"] = modalidade_execucao
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Modalidade de execução inválida; permitido: 1, 2, 3, 4"
    # detail_msg = "value is not a valid enumeration member; permitted: 1, 2, 3, 4"
    assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize(
    "jornada_trabalho_semanal",
    [
        (-2),
        (0),
    ],
)
def test_put_part_invalid_jornada_trabalho_semanal(
    input_part: dict,
    jornada_trabalho_semanal: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_participantes,
    client: Client,
):
    """Tenta submeter um participante com jornada de trabalho semanal inválida"""
    input_part["jornada_trabalho_semanal"] = jornada_trabalho_semanal
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Carga horária semanal deve ser maior que zero"
    assert response.json().get("detail")[0]["msg"] == detail_msg
