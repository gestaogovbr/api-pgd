"""
Testes relacionados ao plano de trabalho do participante.
"""
from datetime import date, timedelta

from httpx import Client
from fastapi import status

import pytest

from util import over_a_year

# grupos de campos opcionais e obrigatórios a testar

fields_plano_trabalho = {
    "optional": (["cancelado"],),
    "mandatory": (
        ["id_plano_entrega_unidade"],
        ["cod_SIAPE_unidade_exercicio"],
        ["cpf_participante"],
        ["data_inicio_plano"],
        ["data_termino_plano"],
        ["carga_horaria_total_periodo_plano"],
        ["contribuicoes"],
        ["consolidacoes"],
    ),
}

fields_contribuicao = {
    "optional": (
        ["descricao_contribuicao"],
        # ["id_entrega"], # obrigatório quando tipo_contribuicao==1
    ),
    "mandatory": (
        ["id_plano_trabalho_participante"],
        ["tipo_contribuicao"],
        ["horas_vinculadas"],
    ),
}

fields_consolidacao = {
    "optional": (["avaliacao_plano_trabalho"],),
    "mandatory": (
        ["data_inicio_registro"],
        ["data_fim_registro"],
    ),
}

# Helper functions


def assert_equal_plano_trabalho(plano_trabalho_1: dict, plano_trabalho_2: dict):
    """Verifica a igualdade de dois planos de trabalho, considerando
    apenas os campos obrigatórios.
    """
    # Compara o conteúdo de todos os campos obrigatórios do plano de
    # trabalho, exceto as listas de contribuições e consolidações
    assert all(
        plano_trabalho_1[attribute] == plano_trabalho_2[attribute]
        for attributes in fields_plano_trabalho["mandatory"]
        for attribute in attributes
        if attribute not in ("contribuicoes", "consolidacoes")
    )

    # Compara o conteúdo de cada contribuição, somente campos obrigatórios
    contribuicoes_1 = set(
        {
            field: value
            for contribuicao in plano_trabalho_1["contribuicoes"]
            for field, value in contribuicao.items()
            if field in fields_contribuicao["mandatory"]
        }
    )
    contribuicoes_2 = set(
        {
            field: value
            for contribuicao in plano_trabalho_2["contribuicoes"]
            for field, value in contribuicao.items()
            if field in fields_contribuicao["mandatory"]
        }
    )
    assert contribuicoes_1 == contribuicoes_2

    # Compara o conteúdo de cada consolidação, somente campos obrigatórios
    consolidacoes_1 = set(
        {
            field: value
            for contribuicao in plano_trabalho_1["consolidacoes"]
            for field, value in contribuicao.items()
            if field in fields_contribuicao["mandatory"]
        }
    )
    consolidacoes_2 = set(
        {
            field: value
            for contribuicao in plano_trabalho_2["consolidacoes"]
            for field, value in contribuicao.items()
            if field in fields_contribuicao["mandatory"]
        }
    )
    assert consolidacoes_1 == consolidacoes_2


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
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert_equal_plano_trabalho(response.json(), input_pt)

    # Consulta API para conferir se a criação foi persistida
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
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
        "/organizacao/3"  # só está autorizado na organização 1
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    detail_message = "Usuário não tem permissão na cod_SIAPE_instituidora informada"
    assert detail_message in response.json().get("detail")


def test_create_plano_trabalho_outra_unidade_admin(
    truncate_pt,  # pylint: disable=unused-argument
    input_pt: dict,
    header_admin: dict,
    admin_credentials: dict,
    client: Client,
):
    """Tenta, como administrador, criar um novo Plano de Trabalho do
    Participante em uma organização diferente da sua própria organização.
    """
    input_pt["cod_SIAPE_instituidora"] = 3 # unidade diferente

    response = client.get(
        f"/user/{admin_credentials['username']}",
        headers=header_admin,
    )

    # Verifica se o usuário é admin e se está em outra unidade
    assert response.status_code == status.HTTP_200_OK
    admin_data = response.json()
    assert (
        admin_data.get("cod_SIAPE_instituidora", None)
        != input_pt["cod_SIAPE_instituidora"]
    )
    assert admin_data.get("is_admin", None) is True

    response = client.put(
        "/organizacao/2"  # organização diferente da do admin
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
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
    input_pt["cod_SIAPE_unidade_exercicio"] = 100  # Valor era 99
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_trabalho(response.json(), input_pt)

    # Consulta API para conferir se a alteração foi persistida
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_trabalho(response.json(), input_pt)


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
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta criar um novo plano de trabalho, sendo que, quando o campo
    tipo_contribuicao tiver valor 1, o campo id_entrega se tornará
    obrigatório.
    """
    input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
    input_pt["contribuicoes"][0]["id_entrega"] = id_entrega
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if tipo_contribuicao == 1 and id_entrega is None:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "O campo id_entrega é obrigatório quando tipo_contribuicao "
            "tiver o valor 1."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    elif tipo_contribuicao == 2 and id_entrega:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Não se deve informar id_entrega quando tipo_contribuicao == 2"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("omitted_fields", enumerate(fields_contribuicao["optional"]))
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

    partial_input_pt["id_plano_trabalho_participante"] = 557 + offset
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{partial_input_pt['id_plano_trabalho_participante']}",
        json=partial_input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("nulled_fields", enumerate(fields_contribuicao["optional"]))
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

    partial_input_pt["id_plano_trabalho_participante"] = 557 + offset
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{partial_input_pt['id_plano_trabalho_participante']}",
        json=partial_input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("omitted_fields", enumerate(fields_consolidacao["optional"]))
def test_create_plano_trabalho_consolidacao_omit_optional_fields(
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
        for consolidacao in partial_input_pt["consolidacoes"]:
            if field in consolidacao:
                del consolidacao[field]

    partial_input_pt["id_plano_trabalho_participante"] = 557 + offset
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{partial_input_pt['id_plano_trabalho_participante']}",
        json=partial_input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("nulled_fields", enumerate(fields_consolidacao["optional"]))
def test_create_plano_trabalho_consolidacao_null_optional_fields(
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
        for consolidacao in partial_input_pt["consolidacoes"]:
            if field in consolidacao:
                consolidacao[field] = None

    partial_input_pt["id_plano_trabalho_participante"] = 557 + offset
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{partial_input_pt['id_plano_trabalho_participante']}",
        json=partial_input_pt,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "missing_fields", enumerate(fields_plano_trabalho["mandatory"])
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
    truncate_pe,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Testa a criação de um plano de trabalho com grande volume de dados."""

    quantidade_planos = 200
    data_inicio_plano = date.fromisoformat(input_pt["data_inicio_plano"])
    data_termino_plano = data_inicio_plano + timedelta(days=quantidade_planos)

    def create_huge_contribuicao():
        contribuicao = input_pt["contribuicoes"][0].copy()
        contribuicao["descricao_contribuicao"] = "x" * 300  # 300 caracteres
        return contribuicao

    def create_huge_consolidacao(day: int):
        consolidacao = input_pt["consolidacoes"][0].copy()
        consolidacao["descricao_consolidacao"] = "x" * 300  # 300 caracteres
        data = (data_inicio_plano + timedelta(days=day)).isoformat()
        consolidacao["data_inicio_registro"] = consolidacao["data_fim_registro"] = data
        return consolidacao

    # prepara a data fim para caber todas as contribuições
    input_pt["data_termino_plano"] = data_termino_plano.isoformat()
    for day in range(quantidade_planos):
        input_pt["contribuicoes"].append(create_huge_contribuicao())
        input_pt["consolidacoes"].append(create_huge_consolidacao(day=day))

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/555",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, descricao_contribuicao",
    [
        (1, "x" * 301),  # ultrapassa o max_length
        (2, "x" * 300),  # limite do max_length
    ],
)
def test_create_pt_exceed_string_max_size(
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    id_plano_trabalho_participante: int,
    descricao_contribuicao: str,  # 300 caracteres
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
    str_max_size: int = 300,
):
    """Testa a criação de um plano de entregas excedendo o tamanho
    máximo de cada campo"""

    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["contribuicoes"][0][
        "descricao_contribuicao"
    ] = descricao_contribuicao  # 300 caracteres

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if len(descricao_contribuicao) > str_max_size:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "String should have at most 300 characters"
        assert response.json().get("detail")[0]["msg"] == detail_message
    else:
        assert response.status_code == status.HTTP_201_CREATED


# TODO: Verbo PATCH poderá ser implementado em versão futura.
#
# @pytest.mark.parametrize(
#     "verb, missing_fields",
#     itertools.product(  # todas as combinações entre
#         ("put", "patch"), fields_plano_trabalho["mandatory"]  # verb  # missing_fields
#     ),
# )
# def test_update_plano_trabalho_missing_mandatory_fields(
#     truncate_pt,
#     verb: str,
#     example_pt,
#     input_pt: dict,
#     missing_fields: list,
#     user1_credentials: dict,
#     header_usr_1: dict,
#     client: Client,
# ):
#     """Tenta atualizar um plano de trabalho faltando campos
#     obrigatórios.

#     Para usar o verbo PUT é necessário passar a representação completa
#     do recurso. Por isso, os campos obrigatórios não podem estar
#     faltando. Para realizar uma atualização parcial, use o método PATCH.

#     Já com o verbo PATCH, os campos omitidos são interpretados como sem
#     alteração. Por isso, é permitido omitir os campos obrigatórios.
#     """
#     for field in missing_fields:
#         del input_pt[field]

#     input_pt["id_plano_trabalho_participante"] = 555  # precisa ser um plano existente
#     call = getattr(client, verb)  # put ou patch
#     response = call(
#         f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
#         f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
#         json=input_pt,
#         headers=header_usr_1,
#     )
#         assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#         assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     elif verb == "patch":
#         assert response.status_code == status.HTTP_200_OK
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     elif verb == "patch":
#         assert response.status_code == status.HTTP_200_OK


# @pytest.mark.parametrize("missing_fields", fields_plano_trabalho["mandatory"])
# def test_patch_plano_trabalho_inexistente(
#     truncate_pt,
#     input_pt: dict,
#     missing_fields: list,
#     user1_credentials: dict,
#     header_usr_1: dict,
#     client: Client,
# ):
#     """Tenta atualizar um plano de trabalho com PATCH, faltando campos
#     obrigatórios.

#     Com o verbo PATCH, os campos omitidos são interpretados como sem
#     alteração. Por isso, é permitido omitir os campos obrigatórios.
#     """
#     for field in missing_fields:
#         del input_pt[field]

#     input_pt["id_plano_trabalho_participante"] = 999  # precisa ser um plano inexistente
#     response = client.patch(
#         f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
#         f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
#         json=input_pt,
#         headers=header_usr_1,
#     )
#     assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, cod_SIAPE_unidade_exercicio, "
    "cpf_participante, "
    "data_inicio_plano, data_termino_plano, "
    "cancelado",
    [
        (101, 99, "64635210600", "2023-01-01", "2023-01-15", False),  # igual ao exemplo
        (102, 99, "64635210600", "2023-02-01", "2023-02-15", False),  # sem sobreposição
        # sobreposição no início
        (103, 99, "64635210600", "2022-12-01", "2023-01-08", False),
        # sobreposição no fim
        (104, 99, "64635210600", "2023-01-30", "2023-02-15", False),
        (
            105,
            99,
            "64635210600",
            "2023-01-02",
            "2023-01-08",
            False,
        ),  # contido no período
        (106, 99, "64635210600", "2022-12-31", "2023-01-16", False),  # contém o período
        (107, 99, "64635210600", "2022-12-01", "2023-01-08", True),  # cancelado
        (108, 100, "64635210600", "2023-01-01", "2023-01-15", False),  # outra unidade
        (
            109,
            99,
            "82893311776",
            "2023-01-01",
            "2023-01-15",
            False,
        ),  # outro participante
        (
            110,
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
    id_plano_trabalho_participante: int,
    cod_SIAPE_unidade_exercicio: int,
    cpf_participante: str,
    data_inicio_plano: str,
    data_termino_plano: str,
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
    input_pt2["id_plano_trabalho_participante"] = 556
    input_pt2["data_inicio_plano"] = "2023-01-16"
    input_pt2["data_termino_plano"] = "2023-01-31"
    input_pt2["consolidacoes"] = [
        {
            "data_inicio_registro": "2023-01-16",
            "data_fim_registro": "2023-01-23",
            "avaliacao_plano_trabalho": 5,
        }
    ]
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt2['id_plano_trabalho_participante']}",
        json=input_pt2,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED

    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["cod_SIAPE_unidade_exercicio"] = cod_SIAPE_unidade_exercicio
    input_pt["cpf_participante"] = cpf_participante
    input_pt["data_inicio_plano"] = data_inicio_plano
    input_pt["data_termino_plano"] = data_termino_plano
    input_pt["cancelado"] = cancelado
    input_pt["consolidacoes"] = []
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if (
        # se algum dos planos estiver cancelado, não há problema em haver
        # sobreposição
        not cancelado
        # se são unidades diferentes, não há problema em haver sobreposição
        and (
            input_pt["cod_SIAPE_unidade_exercicio"]
            == original_pt["cod_SIAPE_unidade_exercicio"]
        )
        # se são participantes diferentes, não há problema em haver
        # sobreposição
        and (input_pt["cpf_participante"] == original_pt["cpf_participante"])
    ):
        if any(
            (
                date.fromisoformat(input_pt["data_inicio_plano"])
                <= date.fromisoformat(existing_pt["data_termino_plano"])
            )
            and (
                date.fromisoformat(input_pt["data_termino_plano"])
                >= date.fromisoformat(existing_pt["data_inicio_plano"])
            )
            for existing_pt in (original_pt, input_pt2)
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "Já existe um plano de trabalho para este "
                "cod_SIAPE_unidade_exercicio para este cpf_participante "
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
    "data_inicio_plano, data_termino_plano",
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
    data_inicio_plano: str,
    data_termino_plano: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Plano de Entregas não pode ter vigência superior a um ano."""
    input_pt["data_inicio_plano"] = data_inicio_plano
    input_pt["data_termino_plano"] = data_termino_plano

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if (
        over_a_year(
            date.fromisoformat(data_termino_plano),
            date.fromisoformat(data_inicio_plano),
        )
        == 1
    ):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Plano de trabalho não pode abranger período maior que 1 ano."
        assert any(
            f"Value error, {detail_message}" == error["msg"]
            for error in response.json().get("detail")
        )
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
    input_pt["id_plano_trabalho_participante"] = 110
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/plano_trabalho/111",
        json=input_pt,
        headers=header_usr_1,  # diferente de 110
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_message = (
        "Parâmetro id_plano_trabalho_participante na URL e no JSON devem ser iguais"
    )
    assert response.json().get("detail", None) == detail_message


def test_get_plano_trabalho(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    example_pt,  # pylint: disable=unused-argument
    client: Client,
):
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
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
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/plano_trabalho/888888888",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

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
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Verifica se a data_termino_plano é maior ou igual à data_inicio_plano."""
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
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Data fim do Plano de Trabalho deve ser maior "
            "ou igual que Data de início."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


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
def test_create_pt_data_consolidacao_out_of_bounds(
    input_pt: dict,
    id_plano_trabalho_participante: int,
    data_inicio_plano: str,
    data_termino_plano: str,
    data_inicio_registro: str,
    data_fim_registro: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Verifica se o registro (consolidação) está dentro intervalo do
    Plano de Trabalho.
    """
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["data_inicio_plano"] = data_inicio_plano
    input_pt["data_termino_plano"] = data_termino_plano
    input_pt["consolidacoes"][0]["data_inicio_registro"] = data_inicio_registro
    input_pt["consolidacoes"][0]["data_fim_registro"] = data_fim_registro

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )
    if (
        date.fromisoformat(data_inicio_registro) < date.fromisoformat(data_inicio_plano)
    ) or (
        date.fromisoformat(data_fim_registro) > date.fromisoformat(data_termino_plano)
    ):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Data de início e de fim de registro devem estar contidos no "
            "período do Plano de Trabalho."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, consolidacoes",
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
def test_create_plano_trabalho_consolidacao_overlapping_date_interval(
    truncate_pt,  # pylint: disable=unused-argument
    input_pt: dict,
    id_plano_trabalho_participante: int,
    consolidacoes: list[tuple[str, str]],
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um plano de trabalho, cujas consolidações tenham
    sobreposição de intervalo de data na mesma unidade para o mesmo
    participante.

    O Plano de Trabalho original é alterado para incluir consolidações
    com diferentes condições de data, conforme o especificado nos
    parâmetros de teste.

    Planos de Trabalho cujas consolidações possuam sobreposição de data
    devem ser rejeitadas.
    """
    original_consolidacao = input_pt["consolidacoes"][0].copy()

    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante

    input_pt["consolidacoes"] = []
    for consolidacao in consolidacoes:
        consolidacao_template = original_consolidacao.copy()
        consolidacao_template["data_inicio_registro"] = consolidacao[0]
        consolidacao_template["data_fim_registro"] = consolidacao[1]
        input_pt["consolidacoes"].append(consolidacao_template)

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    consolidacoes.sort(key=lambda consolidacao: consolidacao[0])
    for consolidacao_1, consolidacao_2 in zip(consolidacoes[:-1], consolidacoes[1:]):
        data_fim_registro_1 = date.fromisoformat(consolidacao_1[1])
        data_inicio_registro_2 = date.fromisoformat(consolidacao_2[0])
        if data_inicio_registro_2 < data_fim_registro_1:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "Uma ou mais consolidações possuem data_inicio_registro e "
                "data_fim_registro sobrepostas."
            )
            assert any(
                f"Value error, {detail_message}" in error["msg"]
                for error in response.json().get("detail")
            )
            return

    assert response.status_code == status.HTTP_201_CREATED
    assert_equal_plano_trabalho(response.json(), input_pt)


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
    truncate_pt,  # pylint: disable=unused-argument
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
    "tipo_contribuicao",
    [(-2), (0), (1), (4)],
)
def test_create_pt_invalid_tipo_contribuicao(
    input_pt: dict,
    tipo_contribuicao: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta submeter um plano de trabalho com tipo_contribuicao inválido"""
    input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if tipo_contribuicao in range(1, 4):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Tipo de contribuição inválida; permitido: 1 a 3"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, tipo_contribuicao, id_plano_entrega_unidade, id_entrega",
    [
        (120, 1, 1, None),
        (121, 1, 1, 1),
        (121, 1, 1, 999),  # id_entrega não existente
        (122, 1, 999, 1),  # id_plano_entrega_unidade não existente
        (123, 2, 1, None),
        (124, 2, 1, 1),
        (125, 3, 1, None),
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
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
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
        f"/plano_entregas/{id_plano_entrega_existente}",
        json=input_pe,
        headers=header_usr_1,
    )

    # Prepara o plano de trabalho com os parâmetros informados no teste
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
    input_pt["contribuicoes"][0]["id_entrega"] = id_entrega

    assert response.status_code == status.HTTP_201_CREATED

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )

    if tipo_contribuicao == 1:
        if not id_entrega:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "O campo id_entrega é obrigatório quando tipo_contribuicao tiver o valor 1"
            assert any(
                f"Value error, {detail_message}" in error["msg"]
                for error in response.json().get("detail")
            )
        elif (
            id_plano_entrega_unidade != id_plano_entrega_existente
            or id_entrega not in ids_entregas_existentes
        ):
            # TODO: Verificar impacto no desempenho com grande volume de requisições
            # e se pode ser aproveitada a verificação de FK no banco
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "Referência a tabela entrega não encontrada"
            assert detail_message in response.json().get("detail")

    elif tipo_contribuicao == 2 and id_entrega:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Não se deve informar id_entrega quando tipo_contribuicao == 2"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


def test_create_pt_duplicate_id_plano(
    truncate_pe,  # pylint: disable=unused-argument
    truncate_pt,  # pylint: disable=unused-argument
    example_pe,  # pylint: disable=unused-argument
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) is None
    assert_equal_plano_trabalho(response.json(), input_pt)


@pytest.mark.parametrize("horas_vinculadas", [-2, -1])
def test_create_pt_invalid_horas_vinculadas(
    input_pt: dict,
    horas_vinculadas: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    input_pt["contribuicoes"][0]["horas_vinculadas"] = horas_vinculadas
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_message = "Valor de horas_vinculadas deve ser maior ou igual a zero"
    assert any(
        f"Value error, {detail_message}" in error["msg"]
        for error in response.json().get("detail")
    )


@pytest.mark.parametrize("avaliacao_plano_trabalho", [0, 1, 2, 5, 6])
def test_create_pt_consolidacoes_invalid_avaliacao_plano_trabalho(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    avaliacao_plano_trabalho: int,
    client: Client,
):
    """Tenta criar uma consolidação com avaliação_plano_trabalho inválido"""
    input_pt["consolidacoes"][0]["avaliacao_plano_trabalho"] = avaliacao_plano_trabalho

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if avaliacao_plano_trabalho in range(1, 6):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Avaliação de plano de trabalho inválida; permitido: 1 a 5"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


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
    """Tenta submeter um plano de trabalho com cpf inválido"""
    input_pt["cpf_participante"] = cpf_participante

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
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
