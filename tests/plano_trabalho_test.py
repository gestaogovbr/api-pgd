"""
Testes relacionados ao plano de trabalho do participante.
"""

from datetime import date
from typing import Optional

from httpx import Client
from fastapi import status

import pytest

from util import over_a_year, assert_error_message

# grupos de campos opcionais e obrigatórios a testar

FIELDS_PLANO_TRABALHO = {
    "optional": tuple(),  # nenhum campo é opcional
    "mandatory": (
        ["origem_unidade"],
        ["cod_unidade_autorizadora"],
        ["id_plano_trabalho"],
        ["status"],
        ["cod_unidade_executora"],
        ["cpf_participante"],
        ["matricula_siape"],
        ["data_inicio"],
        ["data_termino"],
        ["carga_horaria_disponivel"],
        ["contribuicoes"],
        ["avaliacao_registros_execucao"],
    ),
}

FIELDS_CONTRIBUICAO = {
    "optional": (
        ["cod_unidade_autorizadora_externa"],
        ["id_plano_entrega"],
        ["id_entrega"],
    ),
    "mandatory": (
        ["origem_unidade"],
        ["id_contribuicao"],
        ["cod_unidade_instituidora"],
        ["tipo_contribuicao"],
        ["percentual_contribuicao"],
        ["carga_horaria_disponivel"],
    ),
}

FIELDS_AVALIACAO_REGISTROS_EXECUCAO = {
    "optional": tuple(),  # nenhum campo é opcional
    "mandatory": (
        ["id_periodo_avaliativo"],
        ["data_inicio_periodo_avaliativo"],
        ["data_fim_periodo_avaliativo"],
        ["avaliacao_registros_execucao"],
        ["data_avaliacao_registros_execucao"],
        ["cpf_participante"],
        ["data_inicio"],
        ["data_termino"],
        ["carga_horaria_disponivel"],
    ),
}

# Helper functions


def assert_equal_plano_trabalho(plano_trabalho_1: dict, plano_trabalho_2: dict):
    """Verifica a igualdade de dois planos de trabalho, considerando
    apenas os campos obrigatórios.
    """
    # Compara o conteúdo de todos os campos obrigatórios do plano de
    # trabalho, exceto as listas de contribuições e avaliacao_registros_execucao
    assert all(
        plano_trabalho_1[attribute] == plano_trabalho_2[attribute]
        for attributes in FIELDS_PLANO_TRABALHO["mandatory"]
        for attribute in attributes
        if attribute not in ("contribuicoes", "avaliacao_registros_execucao")
    )

    # Compara o conteúdo de cada contribuição, somente campos obrigatórios
    contribuicoes_1 = set(
        {
            field: value
            for contribuicao in plano_trabalho_1["contribuicoes"]
            for field, value in contribuicao.items()
            if field in FIELDS_CONTRIBUICAO["mandatory"]
        }
    )
    contribuicoes_2 = set(
        {
            field: value
            for contribuicao in plano_trabalho_2["contribuicoes"]
            for field, value in contribuicao.items()
            if field in FIELDS_CONTRIBUICAO["mandatory"]
        }
    )
    assert contribuicoes_1 == contribuicoes_2

    # Compara o conteúdo de cada avaliacao_registros_execucao, somente campos obrigatórios
    avaliacao_registros_execucao_1 = set(
        {
            field: value
            for avaliacao in plano_trabalho_1["avaliacao_registros_execucao"]
            for field, value in avaliacao.items()
            if field in FIELDS_AVALIACAO_REGISTROS_EXECUCAO["mandatory"]
        }
    )
    avaliacao_registros_execucao_2 = set(
        {
            field: value
            for avaliacao in plano_trabalho_2["avaliacao_registros_execucao"]
            for field, value in avaliacao.items()
            if field in FIELDS_AVALIACAO_REGISTROS_EXECUCAO["mandatory"]
        }
    )
    assert avaliacao_registros_execucao_1 == avaliacao_registros_execucao_2


# Os testes usam muitas fixtures, então necessariamente precisam de
# muitos argumentos. Além disso, algumas fixtures não retornam um valor
# para ser usado no teste, mas mesmo assim são executadas quando estão
# presentes como um argumento da função.
# A linha abaixo desabilita os warnings do Pylint sobre isso.
# pylint: disable=too-many-arguments


def test_create_plano_trabalho_completo(
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Cria um novo Plano de Trabalho do Participante, em uma unidade
    na qual ele está autorizado, contendo todos os dados necessários.
    """
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert_equal_plano_trabalho(response.json(), input_pt)

    # Consulta API para conferir se a criação foi persistida
    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_trabalho(response.json(), input_pt)


def test_create_plano_trabalho_unidade_nao_permitida(
    input_pt: dict,
    header_usr_2: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta criar um novo Plano de Trabalho do Participante em uma
    organização na qual ele não está autorizado.
    """
    response = client.put(
        "/organizacao/SIAPE/3"  # só está autorizado na organização 1
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    detail_message = "Usuário não tem permissão na cod_unidade_autorizadora informada"
    assert detail_message in response.json().get("detail")


def test_create_plano_trabalho_outra_unidade_admin(
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    input_pt: dict,
    header_admin: dict,
    admin_credentials: dict,
    client: Client,
):
    """Tenta, como administrador, criar um novo Plano de Trabalho do
    Participante em uma organização diferente da sua própria organização.
    """
    input_pt["cod_unidade_autorizadora"] = 3  # unidade diferente

    response = client.get(
        f"/user/{admin_credentials['username']}",
        headers=header_admin,
    )

    # Verifica se o usuário é admin e se está em outra unidade
    assert response.status_code == status.HTTP_200_OK
    admin_data = response.json()
    assert (
        admin_data.get("cod_unidade_autorizadora", None)
        != input_pt["cod_unidade_autorizadora"]
    )
    assert admin_data.get("is_admin", None) is True

    response = client.put(
        "/organizacao/SIAPE/3"  # organização diferente da do admin
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_admin,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert_equal_plano_trabalho(response.json(), input_pt)


def test_update_plano_trabalho(
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    example_pt,  # pylint: disable=unused-argument
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Atualiza um Plano de Trabalho existente usando o método PUT."""
    # A fixture example_pt cria um novo Plano de Trabalho na API
    # Altera um campo do PT e reenvia pra API (update)
    input_pt["cod_unidade_executora"] = 100  # Valor era 99
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_trabalho(response.json(), input_pt)

    # Consulta API para conferir se a alteração foi persistida
    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_trabalho(response.json(), input_pt)


@pytest.mark.parametrize(
    "tipo_contribuicao, cod_unidade_autorizadora_externa, id_plano_entrega, id_entrega",
    [
        (1, None, "1", "1"),
        (1, None, "2", "2"),
        (1, None, None, None),
        (2, None, "1", None),
        (2, None, None, None),
        (3, None, "1", "1"),
        (3, None, None, None),
    ],
)
def test_create_plano_trabalho_id_entrega_check(
    input_pt: dict,
    tipo_contribuicao: int,
    cod_unidade_autorizadora_externa: Optional[int],
    id_plano_entrega: Optional[str],
    id_entrega: Optional[str],
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    client: Client,
):
    """Testa a criação de um novo plano de trabalho, verificando as
    regras de validação para os campos relacionados à contribuição.

    O teste verifica as seguintes regras:

    1. Quando tipo_contribuicao == 1, os campos id_plano_entrega e
       id_entrega são obrigatórios.
    2. Quando tipo_contribuicao == 2, os campos
       cod_unidade_autorizadora_externa, id_plano_entrega e id_entrega
       não devem ser informados.
    3. Quando tipo_contribuicao == 3, os campos
       cod_unidade_autorizadora_externa, id_plano_entrega e id_entrega
       são obrigatórios.
    4. Quando tipo_contribuicao != 3, o campo
       cod_unidade_autorizadora_externa não deve ser informado.

    O teste envia uma requisição PUT para a rota
    "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
    com os dados de entrada atualizados de acordo com os parâmetros
    fornecidos. Verifica se a resposta possui o status HTTP correto (201
    Created ou 422 Unprocessable Entity) e se as mensagens de erro
    esperadas estão presentes na resposta.
    """
    input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
    input_pt["contribuicoes"][0]["id_plano_entrega"] = id_plano_entrega
    input_pt["contribuicoes"][0]["id_entrega"] = id_entrega
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    fields_entrega_externa = (
        cod_unidade_autorizadora_externa,
        id_plano_entrega,
        id_entrega,
    )
    error_messages = []
    if tipo_contribuicao == 1 and (id_plano_entrega is None or id_entrega is None):
        error_messages.append(
            "Os campos id_plano_entrega e id_entrega são obrigatórios "
            "quando tipo_contribuicao tiver o valor 1."
        )
    if tipo_contribuicao == 2 and any(fields_entrega_externa):
        error_messages.append(
            "Não se deve informar cod_unidade_autorizadora_externa, "
            "id_plano_entrega ou id_entrega quando tipo_contribuicao == 2"
        )
    if tipo_contribuicao == 3 and any(
        field is None for field in fields_entrega_externa
    ):
        error_messages.append(
            "Os campos cod_unidade_autorizadora_externa, id_plano_entrega e "
            "id_entrega são obrigatórios quando tipo_contribuicao == 3"
        )
    if tipo_contribuicao != 3 and cod_unidade_autorizadora_externa:
        error_messages.append(
            "Só se deve usar cod_unidade_autorizadora_externa "
            "quando tipo_contribuicao == 3"
        )
    if error_messages:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        for detail_message in error_messages:
            assert_error_message(response, detail_message)
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("omitted_fields", enumerate(FIELDS_CONTRIBUICAO["optional"]))
def test_create_plano_trabalho_contribuicao_omit_optional_fields(
    # fixture example_pe é necessária para cumprir IntegrityConstraint (FK)
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    omitted_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um novo plano de trabalho omitindo campos opcionais"""
    partial_input_pt = input_pt.copy()
    offset, field_list = omitted_fields
    for field in field_list:
        for contribuicao in partial_input_pt["contribuicoes"]:
            if field in contribuicao:
                del contribuicao[field]

    partial_input_pt["id_plano_trabalho"] = 557 + offset
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{partial_input_pt['id_plano_trabalho']}",
        json=partial_input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("nulled_fields", enumerate(FIELDS_CONTRIBUICAO["optional"]))
def test_create_plano_trabalho_contribuicao_null_optional_fields(
    # fixture example_pe é necessária para cumprir IntegrityConstraint (FK)
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    nulled_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um novo plano de trabalho enviando null nos campos opcionais"""
    partial_input_pt = input_pt.copy()
    offset, field_list = nulled_fields
    for field in field_list:
        for contribuicao in partial_input_pt["contribuicoes"]:
            if field in contribuicao:
                contribuicao[field] = None

    partial_input_pt["id_plano_trabalho"] = 557 + offset
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{partial_input_pt['id_plano_trabalho']}",
        json=partial_input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "missing_fields", enumerate(FIELDS_PLANO_TRABALHO["mandatory"])
)
def test_create_plano_trabalho_missing_mandatory_fields(
    input_pt: dict,
    missing_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
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

    input_pt["id_plano_trabalho"] = f"{1800 + offset}"  # precisa ser um novo plano
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{example_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "id_plano_trabalho, cod_unidade_executora, cpf_participante, "
    "data_inicio, data_termino, "
    "cancelado",
    [
        (
            "101",
            99,
            "64635210600",
            "2023-01-01",
            "2023-01-15",
            False,
        ),  # igual ao exemplo
        (
            "102",
            99,
            "64635210600",
            "2023-02-01",
            "2023-02-15",
            False,
        ),  # sem sobreposição
        # sobreposição no início
        ("103", 99, "64635210600", "2022-12-01", "2023-01-08", False),
        # sobreposição no fim
        ("104", 99, "64635210600", "2023-01-30", "2023-02-15", False),
        (
            "105",
            99,
            "64635210600",
            "2023-01-02",
            "2023-01-08",
            False,
        ),  # contido no período
        (
            "106",
            99,
            "64635210600",
            "2022-12-31",
            "2023-01-16",
            False,
        ),  # contém o período
        ("107", 99, "64635210600", "2022-12-01", "2023-01-08", True),  # cancelado
        ("108", 100, "64635210600", "2023-01-01", "2023-01-15", False),  # outra unidade
        (
            "109",
            99,
            "82893311776",
            "2023-01-01",
            "2023-01-15",
            False,
        ),  # outro participante
        (
            "110",
            100,
            "82893311776",
            "2023-01-01",
            "2023-01-15",
            False,
        ),  # ambos diferentes
    ],
)
def test_create_plano_trabalho_overlapping_date_interval(
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    example_pt,  # pylint: disable=unused-argument
    input_pt: dict,
    id_plano_trabalho: str,
    cod_unidade_executora: int,
    cpf_participante: str,
    data_inicio: str,
    data_termino: str,
    cancelado: bool,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de trabalho com sobreposição de intervalo de
    data na mesma unidade para o mesmo participante.

    O Plano de Trabalho original é criado e então é testada a criação de
    cada novo Plano de Trabalho, com sobreposição ou não das datas, sendo
    da mesma ou outra unidade, de mesmo ou outro participante, conforme
    especificado nos parâmetros de teste.
    """
    original_pt = input_pt.copy()
    input_pt2 = original_pt.copy()
    input_pt2["id_plano_trabalho"] = "556"
    input_pt2["data_inicio"] = "2023-01-16"
    input_pt2["data_termino"] = "2023-01-31"
    input_pt2["avaliacao_registros_execucao"] = [
        {
            "id_periodo_avaliativo": "string",
            "data_inicio_periodo_avaliativo": "2023-01-16",
            "data_fim_periodo_avaliativo": "2023-01-23",
            "avaliacao_registros_execucao": 5,
            "data_avaliacao_registros_execucao": "2023-01-03",
            "cpf_participante": "64635210600",
            "data_inicio": "2023-01-16",
            "data_termino": "2023-01-31",
            "carga_horaria_disponivel": 80,
        }
    ]
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt2['id_plano_trabalho']}",
        json=input_pt2,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED

    input_pt["id_plano_trabalho"] = id_plano_trabalho
    input_pt["cod_unidade_executora"] = cod_unidade_executora
    input_pt["cpf_participante"] = cpf_participante
    input_pt["data_inicio"] = data_inicio
    input_pt["data_termino"] = data_termino
    input_pt["cancelado"] = cancelado
    input_pt["avaliacao_registros_execucao"] = []
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if (
        # se algum dos planos estiver cancelado, não há problema em haver
        # sobreposição
        not cancelado
        # se são unidades diferentes, não há problema em haver sobreposição
        and (input_pt["cod_unidade_executora"] == original_pt["cod_unidade_executora"])
        # se são participantes diferentes, não há problema em haver
        # sobreposição
        and (input_pt["cpf_participante"] == original_pt["cpf_participante"])
    ):
        if any(
            (
                date.fromisoformat(input_pt["data_inicio"])
                <= date.fromisoformat(existing_pt["data_termino"])
            )
            and (
                date.fromisoformat(input_pt["data_termino"])
                >= date.fromisoformat(existing_pt["data_inicio"])
            )
            for existing_pt in (original_pt, input_pt2)
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "Já existe um plano de trabalho para esta "
                "cod_unidade_executora para este cpf_participante "
                "no período informado."
            )
            assert response.json().get("detail", None) == detail_msg
        else:
            # não há sobreposição de datas
            assert response.status_code == status.HTTP_201_CREATED
            assert_equal_plano_trabalho(response.json(), input_pt)
    else:
        # um dos planos está cancelado, deve ser criado
        assert response.status_code == status.HTTP_201_CREATED
        assert_equal_plano_trabalho(response.json(), input_pt)


@pytest.mark.parametrize(
    "data_inicio, data_termino",
    [
        ("2023-01-01", "2023-06-30"),  # igual ao exemplo
        ("2023-01-01", "2024-01-01"),  # um ano
        ("2023-01-01", "2024-01-02"),  # mais que um ano
    ],
)
def test_create_plano_trabalho_date_interval_over_a_year(
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    data_inicio: str,
    data_termino: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Plano de Entregas não pode ter vigência superior a um ano."""
    input_pt["data_inicio"] = data_inicio
    input_pt["data_termino"] = data_termino

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
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
        detail_message = "Plano de trabalho não pode abranger período maior que 1 ano."
        assert_error_message(response, detail_message)
    else:
        assert response.status_code == status.HTTP_201_CREATED
        assert_equal_plano_trabalho(response.json(), input_pt)


def test_create_pt_cod_plano_inconsistent(
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de trabalho com um códigos diferentes
    informados na URL e no campo id_plano_trabalho do JSON.
    """
    input_pt["id_plano_trabalho"] = "110"
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        "/plano_trabalho/111",
        json=input_pt,
        headers=header_usr_1,  # diferente de "110"
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_message = "Parâmetro id_plano_trabalho na URL e no JSON devem ser iguais"
    assert response.json().get("detail", None) == detail_message


def test_get_plano_trabalho(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    example_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Consulta um plano de trabalho."""
    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        headers=header_usr_1,
    )

    # Inclui os campos de resposta do json que não estavam no template
    input_pt["cancelado"] = False
    input_pt["contribuicoes"][1]["id_entrega"] = None
    input_pt["contribuicoes"][1]["descricao_contribuicao"] = None

    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_trabalho(response.json(), input_pt)


def test_get_pt_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    """Tenta acessar um plano de trabalho inexistente."""
    response = client.get(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        "/plano_trabalho/888888888",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert response.json().get("detail", None) == "Plano de trabalho não encontrado"


def test_get_pt_different_unit(
    input_pt: dict,
    header_usr_2: dict,
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    example_pt_unidade_3,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta acessar um plano de trabalho de uma unidade diferente, à
    qual o usuário não tem acesso."""
    response = client.get(
        "/organizacao/SIAPE/3"  # Sem autorização nesta unidade
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_pt_different_unit_admin(
    input_pt: dict,
    header_admin: dict,
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    example_pt_unidade_3,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta acessar um plano de trabalho de uma unidade diferente, mas
    com um usuário com permissão de admin."""
    response = client.get(
        f"/organizacao/SIAPE/3"  # Unidade diferente
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        headers=header_admin,
    )

    # Inclui os campos de resposta do json que não estavam no template
    input_pt["status"] = 3
    input_pt["cod_unidade_executora"] = 3
    input_pt["carga_horaria_disponivel"] = input_pt["carga_horaria_disponivel"]
    input_pt["avaliacao_registros_execucao"][0][
        "data_avaliacao_registros_execucao"
    ] = "2023-01-03"

    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_trabalho(response.json(), input_pt)


@pytest.mark.parametrize(
    "id_plano_trabalho, data_inicio, data_termino",
    [
        (77, "2020-06-04", "2020-04-01"),
        (78, "2020-06-04", "2020-04-01"),
        (79, "2020-06-04", "2020-04-01"),
    ],
)
def test_create_pt_invalid_dates(
    input_pt: dict,
    id_plano_trabalho: str,
    data_inicio: str,
    data_termino: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Verifica se a data_termino_plano é maior ou igual à data_inicio_plano."""
    input_pt["data_inicio"] = data_inicio
    input_pt["data_termino"] = data_termino
    input_pt["id_plano_trabalho"] = id_plano_trabalho

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        "/plano_trabalho",
        json=input_pt,
        headers=header_usr_1,
    )
    if data_inicio > data_termino:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Data fim do Plano de Trabalho deve ser maior "
            "ou igual que Data de início."
        )
        assert_error_message(response, detail_message)
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_trabalho, data_inicio, data_termino, "
    "data_inicio_periodo_avaliativo, data_fim_periodo_avaliativo",
    [
        (80, "2023-06-04", "2023-06-11", "2023-04-01", "2023-04-02"),
        (81, "2023-06-04", "2023-06-11", "2024-04-01", "2023-04-02"),
        (82, "2023-06-04", "2023-06-11", "2021-04-02", "2023-06-02"),
        (83, "2023-04-01", "2023-04-01", "2023-06-01", "2023-06-02"),
        (84, "2023-04-01", "2023-04-01", "2023-04-01", "2023-04-01"),
    ],
)
def test_create_pt_data_avaliacao_out_of_bounds(
    input_pt: dict,
    id_plano_trabalho: int,
    data_inicio: str,
    data_termino: str,
    data_inicio_periodo_avaliativo: str,
    data_fim_periodo_avaliativo: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    client: Client,
):
    """Verifica se o período de avaliação do registro de execução está
    dentro do intervalo do Plano de Trabalho.
    """
    input_pt["id_plano_trabalho"] = id_plano_trabalho
    input_pt["data_inicio"] = data_inicio
    input_pt["data_termino"] = data_termino
    input_pt["avaliacao_registros_execucao"][0][
        "data_inicio_periodo_avaliativo"
    ] = data_inicio_periodo_avaliativo
    input_pt["avaliacao_registros_execucao"][0][
        "data_fim_periodo_avaliativo"
    ] = data_fim_periodo_avaliativo

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        "/plano_trabalho",
        json=input_pt,
        headers=header_usr_1,
    )
    if (
        date.fromisoformat(data_inicio_periodo_avaliativo)
        < date.fromisoformat(data_inicio)
    ) or (
        date.fromisoformat(data_fim_periodo_avaliativo)
        > date.fromisoformat(data_termino)
    ):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Data de início e de fim do período de avaliação do registro "
            "de execução devem estar contidos no período do Plano de Trabalho."
        )
        assert_error_message(response, detail_message)
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_trabalho, periodo_avaliativo",
    [
        (101, [("2023-01-01", "2023-01-02")]),  # igual ao exemplo
        (
            102,
            [("2023-01-01", "2023-01-07"), ("2023-01-08", "2023-01-15")],
        ),  # sem sobreposição
        (
            103,
            [("2023-01-07", "2023-01-15"), ("2023-01-01", "2023-01-07")],
        ),  # sobreposição no início
        (
            104,
            [("2023-01-01", "2023-01-08"), ("2023-01-07", "2023-01-15")],
        ),  # sobreposição no fim
        (
            105,
            [
                ("2023-01-01", "2023-01-06"),
                ("2023-01-06", "2023-01-11"),
                ("2023-01-11", "2023-01-15"),
            ],
        ),  # sobreposições múltiplas
        (
            106,
            [("2023-01-01", "2023-01-14"), ("2023-01-02", "2023-01-13")],
        ),  # contido no período
        (
            107,
            [("2023-01-02", "2023-01-14"), ("2023-01-01", "2023-01-15")],
        ),  # contém o período
    ],
)
def test_create_plano_trabalho_avaliacao_overlapping_date_interval(
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    id_plano_trabalho: int,
    periodo_avaliativo: list[tuple[str, str]],
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de trabalho, cujas avaliações de registros de
    execução tenham sobreposição de intervalo de data na mesma unidade
    para o mesmo participante.

    O Plano de Trabalho original é alterado para incluir avaliações de
    registros de execução com diferentes condições de data, conforme o
    especificado nos parâmetros de teste.

    Planos de Trabalho cujas avaliações de registros de execução possuam
    sobreposição de data devem ser rejeitadas.
    """
    original_avaliacao = input_pt["avaliacao_registros_execucao"][0].copy()

    input_pt["id_plano_trabalho"] = id_plano_trabalho

    input_pt["avaliacao_registros_execucao"] = []
    for avaliacao in periodo_avaliativo:
        avaliacao_template = original_avaliacao.copy()
        avaliacao_template["data_inicio_periodo_avaliativo"] = avaliacao[0]
        avaliacao_template["data_fim_periodo_avaliativo"] = avaliacao[1]
        input_pt["avaliacao_registros_execucao"].append(avaliacao_template)

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    periodo_avaliativo.sort(key=lambda avaliacao: avaliacao[0])
    for avaliacao_1, avaliacao_2 in zip(
        periodo_avaliativo[:-1], periodo_avaliativo[1:]
    ):
        data_fim_periodo_avaliativo_1 = date.fromisoformat(avaliacao_1[1])
        data_inicio_periodo_avaliativo_2 = date.fromisoformat(avaliacao_2[0])
    if data_inicio_periodo_avaliativo_2 < data_fim_periodo_avaliativo_1:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Uma ou mais avaliações de registros de execução possuem "
            "data_inicio_periodo_avaliativo e data_fim_periodo_avaliativo sobrepostas."
        )
        assert_error_message(response, detail_message)
        return

    assert response.status_code == status.HTTP_201_CREATED
    assert_equal_plano_trabalho(response.json(), input_pt)


@pytest.mark.parametrize(
    "tipo_contribuicao, percentual_contribuicao",
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
    percentual_contribuicao: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """
    Verifica se o endpoint de criação de Plano de Trabalho rejeita a
    requisição quando algum campo obrigatório da contribuição está
    faltando.
    """
    id_plano_trabalho = "111222333"
    input_pt["id_plano_trabalho"] = id_plano_trabalho
    input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
    input_pt["contribuicoes"][0]["percentual_contribuicao"] = percentual_contribuicao

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{id_plano_trabalho}",
        json=input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "tipo_contribuicao",
    [(-2), (0), (4)],
)
def test_create_pt_invalid_tipo_contribuicao(
    input_pt: dict,
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    tipo_contribuicao: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """
    Verifica se o endpoint de criação de Plano de Trabalho rejeita a
    requisição quando o tipo de contribuição é inválido.
    """
    input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if tipo_contribuicao in [1, 2, 3]:
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Tipo de contribuição inválida; permitido: 1 a 3"
        assert_error_message(response, detail_message)


def test_create_pt_duplicate_id_plano(
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Testa a criação de um plano de trabalho com um ID de plano de
    trabalho existente.

    O teste envia duas requisições PUT para a mesma rota, com os mesmos
    dados de entrada. Na primeira requisição, espera-se que o status da
    resposta seja 201 Created. Na segunda requisição, espera-se que o
    status da resposta seja 200 OK, e que a resposta não contenha uma
    mensagem de erro. Também verifica se os dados do plano de trabalho na
    resposta são iguais aos dados de entrada.
    """
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) is None
    assert_equal_plano_trabalho(response.json(), input_pt)


@pytest.mark.parametrize("carga_horaria_disponivel", [-2, -1])
def test_create_pt_invalid_carga_horaria_disponivel(
    input_pt: dict,
    carga_horaria_disponivel: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Testa a criação de um plano de trabalho com um valor inválido para
    o campo carga_horaria_disponivel.

    O teste envia uma requisição PUT para a rota
    "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
    com um valor negativo para o campo carga_horaria_disponivel.
    Espera-se que a resposta tenha o status HTTP 422 Unprocessable Entity
    e que a mensagem de erro "Valor de carga_horaria_disponivel deve ser
    maior ou igual a zero" esteja presente na resposta.
    """
    input_pt["carga_horaria_disponivel"] = carga_horaria_disponivel
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_message = "Valor de carga_horaria_disponivel deve ser maior ou igual a zero"
    assert_error_message(response, detail_message)


@pytest.mark.parametrize("avaliacao_registros_execucao", [0, 1, 2, 5, 6])
def test_create_pt_invalid_avaliacao_registros_execucao(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    avaliacao_registros_execucao: int,
    client: Client,
):
    """Testa a criação de um plano de trabalho com um valor inválido para
    o campo avaliacao_registros_execucao.

    O teste envia uma requisição PUT para a rota
    "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
    com diferentes valores campo avaliacao_registros_execucao.
    Quando o valor for válido (entre 1 e 5), espera-se que a resposta
    tenha o status HTTP 201 Created. Quando o valor for inválido,
    espera-se que a resposta tenha o status HTTP 422 Unprocessable Entity
    e que a mensagem de erro "Avaliação de registros de execução
    inválida; permitido: 1 a 5" esteja presente na resposta.
    """
    input_pt["avaliacao_registros_execucao"][0][
        "avaliacao_registros_execucao"
    ] = avaliacao_registros_execucao

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if avaliacao_registros_execucao in range(1, 6):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Avaliação de registros de execução inválida; permitido: 1 a 5"
        assert_error_message(response, detail_message)


@pytest.mark.parametrize(
    "cpf_participante",
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
def test_put_plano_trabalho_invalid_cpf(
    input_pt: dict,
    cpf_participante: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Testa o envio de um plano de trabalho com um CPF inválido.

    O teste envia uma requisição PUT para a rota
    "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
    com um valor inválido para o campo cpf_participante. Espera-se que a
    resposta tenha o status HTTP 422 Unprocessable Entity e que uma das
    seguintes mensagens de erro esteja presente na resposta: - "Dígitos
    verificadores do CPF inválidos." - "CPF inválido." - "CPF precisa ter
    11 dígitos." - "CPF deve conter apenas dígitos."
    """
    input_pt["cpf_participante"] = cpf_participante

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
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
