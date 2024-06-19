"""
Testes relacionados aos status de participantes.
"""

from datetime import date, datetime, timedelta

from httpx import Client

from fastapi import status

import pytest

# Relação de campos obrigatórios para testar sua ausência:
FIELDS_PARTICIPANTES = {
    "optional": tuple(),  # nenhum campo é opcional
    "mandatory": (
        ["origem_unidade"],
        ["cod_unidade_autorizadora"],
        ["cod_unidade_lotacao"],
        ["cpf"],
        ["matricula_siape"],
        ["cod_unidade_instituidora"],
        ["situacao"],
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
    for fields in FIELDS_PARTICIPANTES["optional"]:
        for field in fields:
            if field in data and data[field] is None:
                del data[field]
    return data


def parse_datetimes(data: dict) -> dict:
    """Parse datetimes from the data."""
    if isinstance(data["data_assinatura_tcr"], str):
        data["data_assinatura_tcr"] = datetime.fromisoformat(
            data["data_assinatura_tcr"]
        )
    return data


def assert_equal_participante(participante_1: dict, participante_2: dict):
    """Verifica a igualdade de dois participantes, considerando
    apenas os campos obrigatórios.
    """
    assert parse_datetimes(
        remove_null_optional_fields(participante_1.copy())
    ) == parse_datetimes(remove_null_optional_fields(participante_2.copy()))


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
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert_equal_participante(response.json(), input_part)


def test_put_participante_unidade_nao_permitida(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    header_usr_2: dict,
    client: Client,
):
    """
    Testa a submissão de um participante em outra unidade autorizadora
    (user não é admin)
    """
    response = client.put(
        f"/organizacao/SIAPE/3/3/participante/{input_part['cpf']}",
        json=input_part,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    detail_msg = "Usuário não tem permissão na cod_unidade_autorizadora informada"
    assert response.json().get("detail", None) == detail_msg


def test_put_participante_outra_unidade_admin(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    header_admin: dict,
    admin_credentials: dict,
    client: Client,
):
    """Testa, usando usuário admin, a submissão de um participante em outra
    unidade autorizadora
    """
    input_part["cod_unidade_autorizadora"] = 3  # unidade diferente
    input_part["cod_unidade_lotacao"] = 30  # unidade diferente

    response = client.get(
        f"/user/{admin_credentials['username']}",
        headers=header_admin,
    )

    # Verifica se o usuário é admin e se está em outra unidade
    assert response.status_code == status.HTTP_200_OK
    admin_data = response.json()
    assert (
        admin_data.get("cod_unidade_autorizadora", None)
        != input_part["cod_unidade_autorizadora"]
    )
    assert admin_data.get("is_admin", None) is True

    response = client.put(
        f"/organizacao/SIAPE/{input_part['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_admin,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert_equal_participante(response.json(), input_part)


@pytest.mark.parametrize(
    (
        "cod_unidade_autorizadora_1, cod_unidade_autorizadora_2, "
        "cod_unidade_lotacao_1, cod_unidade_lotacao_2, "
        "matricula_siape_1, matricula_siape_2"
    ),
    [
        # mesmas unidades, mesma matrícula SIAPE
        (1, 1, 10, 10, "1237654", "1237654"),
        # unidades autorizadoras diferentes, mesma matrícula SIAPE
        (1, 2, 10, 20, "1237654", "1237654"),
        # unidades de lotação diferentes, mesma matrícula SIAPE
        (1, 1, 10, 11, "1237654", "1237654"),
        # mesma unidade, matrículas diferentes
        (1, 1, 10, 10, "1237654", "1230054"),
        # unidades diferentes, matrículas diferentes
        (1, 2, 10, 20, "1237654", "1230054"),
    ],
)
def test_put_duplicate_participante(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    cod_unidade_autorizadora_1: int,
    cod_unidade_autorizadora_2: int,
    cod_unidade_lotacao_1: int,
    cod_unidade_lotacao_2: int,
    matricula_siape_1: str,
    matricula_siape_2: str,
    user1_credentials: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    client: Client,
):
    """
    Testa o envio de um mesmo participantes com a mesma matrícula SIAPE.
    O comportamento do segundo envio será testado conforme o caso.

    Sendo a mesma matrícula na mesma unidade autorizadora e de lotação,
    o registro será atualizado e retornará o código HTTP 200 Ok.
    Se a unidade e/ou a matrícula forem diferentes, entende-se que será
    criado um novo registro e será retornado o código HTTP 201 Created.
    """
    input_part["cod_unidade_autorizadora"] = cod_unidade_autorizadora_1
    input_part["cod_unidade_lotacao"] = cod_unidade_lotacao_1
    input_part["matricula_siape"] = matricula_siape_1
    response = client.put(
        f"/organizacao/SIAPE/{cod_unidade_autorizadora_1}"
        f"/{cod_unidade_lotacao_1}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert_equal_participante(response.json(), input_part)

    if cod_unidade_autorizadora_2 == user1_credentials["cod_unidade_autorizadora"]:
        header_usr = header_usr_1
    else:
        header_usr = header_usr_2
    input_part["cod_unidade_autorizadora"] = cod_unidade_autorizadora_2
    input_part["cod_unidade_lotacao"] = cod_unidade_lotacao_2
    input_part["matricula_siape"] = matricula_siape_2
    response = client.put(
        f"/organizacao/SIAPE/{cod_unidade_autorizadora_2}"
        f"/{cod_unidade_lotacao_2}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr,
    )

    if (
        (cod_unidade_autorizadora_1 == cod_unidade_autorizadora_2)
        and (cod_unidade_lotacao_1 == cod_unidade_lotacao_2)
        and (matricula_siape_1 == matricula_siape_2)
    ):
        assert response.status_code == status.HTTP_200_OK
    else:
        assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert_equal_participante(response.json(), input_part)


def test_create_participante_inconsistent(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta submeter participante inconsistente (URL difere do JSON)"""
    nova_matricula = "3311776"
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{nova_matricula}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro matricula_siape na URL e no JSON devem ser iguais"
    assert response.json().get("detail", None) == detail_msg


@pytest.mark.parametrize("missing_fields", enumerate(FIELDS_PARTICIPANTES["mandatory"]))
def test_put_participante_missing_mandatory_fields(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    missing_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta submeter participantes faltando campos obrigatórios"""
    matricula_siape = input_part["matricula_siape"]
    cod_unidade_lotacao = input_part['cod_unidade_lotacao']
    offset, field_list = missing_fields
    for field in field_list:
        del input_part[field]

    input_part["matricula_siape"] = (
        f"{1800000 + offset}"  # precisa ser um novo participante
    )
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{cod_unidade_lotacao}"
        f"/participante/{matricula_siape}",
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
    """Tenta ler os dados de um participante pelo cpf."""
    response = client.get(
        f"/organizacao/SIAPE/{input_part['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK
    assert_equal_participante(response.json(), input_part)


def test_get_participante_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    """Tenta consultar um participante que não existe na base de dados."""
    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        "/1"  # cod_unidade_lotacao
        "/participante/3311776",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail", None) == "Participante não encontrado"


def test_get_participante_different_unit(
    truncate_participantes,  # pylint: disable=unused-argument
    example_part_unidade_3,  # pylint: disable=unused-argument
    input_part: dict,
    header_usr_2: dict,
    client: Client,
):
    """
    Testa ler um participante em outra unidade autorizadora
    (user não é admin)
    """

    input_part["cod_unidade_autorizadora"] = 3

    response = client.get(
        f"/organizacao/SIAPE/{input_part['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    detail_msg = "Usuário não tem permissão na cod_unidade_autorizadora informada"
    assert response.json().get("detail", None) == detail_msg


def test_get_participante_different_unit_admin(
    truncate_participantes,  # pylint: disable=unused-argument
    example_part_unidade_3,  # pylint: disable=unused-argument
    header_admin: dict,
    input_part: dict,
    client: Client,
):
    """Testa ler um participante em outra unidade autorizadora
    (user é admin)"""

    input_part["cod_unidade_autorizadora"] = 3

    response = client.get(
        f"/organizacao/{input_part['origem_unidade']}"
        f"/{input_part['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        headers=header_admin,
    )
    assert response.status_code == status.HTTP_200_OK
    assert_equal_participante(response.json(), input_part)


@pytest.mark.parametrize(
    "matricula_siape",
    [
        ("12345678"),
        ("0000000"),
        ("9999999"),
        ("123456"),
        ("-123456"),
        ("abcdefg"),
    ],
)
def test_put_participante_invalid_matricula_siape(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    matricula_siape: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta submeter um participante com matricula_siape inválida."""

    input_part["matricula_siape"] = matricula_siape

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_messages = [
        "Matricula SIAPE deve ser numérica.",
        "Matrícula SIAPE deve ter 7 dígitos.",
        "Matricula SIAPE inválida.",
    ]
    received_error = response.json().get("detail")
    if isinstance(received_error, str):
        assert any(
            message in received_error
            for message in detail_messages
        )
    else:
        assert any(
            f"Value error, {message}" in error["msg"]
            for message in detail_messages
            for error in received_error
        )


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
    """Tenta submeter um participante com cpf inválido."""
    input_part["cpf"] = cpf_participante

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
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
    "situacao",
    [
        (3),
        (-1),
    ],
)
def test_put_part_invalid_ativo(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    situacao: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um participante com flag participante
    com valor inválido."""
    input_part["situacao"] = situacao
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_messages = "Valor do campo 'situacao' inválido; permitido: 0, 1"
    assert any(
        f"Value error, {message}" in error["msg"]
        for message in detail_messages
        for error in response.json().get("detail")
    )


@pytest.mark.parametrize("modalidade_execucao", [(0), (-1), (6)])
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
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_messages = "Modalidade de execução inválida; permitido: 1, 2, 3, 4, 5"
    assert any(
        f"Value error, {message}" in error["msg"]
        for message in detail_messages
        for error in response.json().get("detail")
    )


def test_put_invalid_data_assinatura_tcr(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um participante com data futura do TCR."""
    # data de amanhã
    input_part["data_assinatura_tcr"] = date.today() + timedelta(days=1)
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_messages = "A data_assinatura_tcr não pode ser data futura."
    assert any(
        f"Value error, {message}" in error["msg"]
        for message in detail_messages
        for error in response.json().get("detail")
    )


def test_put_data_assinatura_tcr_default_value(
    truncate_participantes,  # pylint: disable=unused-argument
    input_part: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Verifica se ao criar um participante e o campo data_assinatura_tcr
    for ausente ou NULL o mesmo é interpretado como FALSE."""
    input_part["data_assinatura_tcr"] = None
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_usr_1,
    )
    assert response.json().get("data_assinatura_tcr") is False
