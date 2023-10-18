"""
Testes relacionados ao plano de trabalho do participante.
"""
import itertools
from datetime import date, timedelta

from httpx import Client

from fastapi import status

import pytest


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

# Os testes usam muitas fixtures, então necessariamente precisam de
# muitos argumentos. Além disso, algumas fixtures não retornam um valor
# para ser usado no teste, mas mesmo assim são executadas quando estão
# presentes como um argumento da função.
# A linha abaixo desabilita os warnings do Pylint sobre isso.
# pylint: disable=too-many-arguments


def test_create_plano_trabalho_completo(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
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
    assert all(
        response.json()[attribute] == input_pt[attribute]
        for attributes in fields_plano_trabalho["mandatory"]
        for attribute in attributes
        if attribute not in ("contribuicoes", "consolidacoes")
    )

    # Consulta API para conferir se a criação foi persistida
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert all(
        response.json()[attribute] == input_pt[attribute]
        for attributes in fields_plano_trabalho["mandatory"]
        for attribute in attributes
        if attribute not in ("contribuicoes", "consolidacoes")
    )


def test_create_plano_trabalho_unidade_nao_permitida(
    input_pt: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta criar um novo Plano de Trabalho do Participante em uma
    organização na qual ele não está autorizado.
    """
    response = client.put(
        f"/organizacao/2"  # só está autorizado na organização 1
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        response.json().get("detail", None)
        == "Usuário não tem permissão na cod_SIAPE_instituidora informada"
    )


def test_update_plano_trabalho(
    input_pt: dict,
    example_pt,  # pylint: disable=unused-argument
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
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

    assert response.status_code == status.HTTP_201_CREATED
    assert all(
        response.json()[attribute] == input_pt[attribute]
        for attributes in fields_plano_trabalho["mandatory"]
        for attribute in attributes
        if attribute not in ("contribuicoes", "consolidacoes")
    )

    # Consulta API para conferir se a alteração foi persistida
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho_participante']}",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert all(
        response.json()[attribute] == input_pt[attribute]
        for attributes in fields_plano_trabalho["mandatory"]
        for attribute in attributes
        if attribute not in ("contribuicoes", "consolidacoes")
    )


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
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == input_pt


@pytest.mark.parametrize("omitted_fields", enumerate(fields_consolidacao["optional"]))
def test_create_plano_trabalho_consolidacao_omit_optional_fields(
    input_pt: dict,
    omitted_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta criar um novo plano de trabalho omitindo campos opcionais"""

    offset, field_list = omitted_fields
    for field in field_list:
        for consolidacao in input_pt["consolidacoes"]:
            if field in consolidacao:
                del consolidacao[field]

    input_pt["id_plano_entrega_unidade"] = 557 + offset
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
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
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Testa a criação de um plano de trabalho com grande volume de dados."""

    def create_huge_contribuicao():
        contribuicao = input_pt["contribuicoes"][0].copy()
        contribuicao["descricao_contribuicao"] = "x" * 1000000  # 1mi de caracteres
        return contribuicao

    def create_huge_consolidacao():
        consolidacao = input_pt["consolidacoes"][0].copy()
        consolidacao["descricao_consolidacao"] = "x" * 1000000  # 1mi de caracteres
        return consolidacao

    for _ in range(200):
        input_pt["contribuicoes"].append(create_huge_contribuicao())
        input_pt["consolidacoes"].append(create_huge_consolidacao())

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/555",
        json=input_pt,
        headers=header_usr_1,
    )

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
    "data_inicio_plano, data_termino_plano",
    [
        (101, 99, 64635210600, "2023-01-01", "2023-01-15"),  # igual ao exemplo
        (102, 99, 64635210600, "2023-01-06", "2023-01-31"),  # sem sobreposição
        (103, 99, 64635210600, "2022-12-01", "2023-01-08"),  # sobreposição no início
        (104, 99, 64635210600, "2023-01-09", "2023-01-31"),  # sobreposição no fim
        (105, 99, 64635210600, "2023-01-02", "2023-01-08"),  # contido no período
        (106, 99, 64635210600, "2022-12-31", "2023-01-16"),  # contém o período
        (105, 100, 64635210600, "2023-01-01", "2023-01-15"),  # outra unidade
        (105, 99, 82893311776, "2023-01-01", "2023-01-15"),  # outro participante
        (105, 100, 82893311776, "2023-01-01", "2023-01-15"),  # ambos diferentes
    ],
)
def test_create_plano_trabalho_overlapping_date_interval(
    truncate_pt,  # pylint: disable=unused-argument
    input_pt: dict,
    id_plano_trabalho_participante: int,
    cod_SIAPE_unidade_exercicio: int,
    cpf_participante: int,
    data_inicio_plano: str,
    data_termino_plano: str,
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

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pt['id_plano_trabalho_participante']}",
        json=original_pt,
        headers=header_usr_1,
    )

    assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)

    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["cod_SIAPE_unidade_exercicio"] = cod_SIAPE_unidade_exercicio
    input_pt["cpf_participante"] = cpf_participante
    input_pt["data_inicio_plano"] = data_inicio_plano
    input_pt["data_termino_plano"] = data_termino_plano

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if (
        # se são unidades diferentes, não há problema em haver sobreposição
        (
            input_pt["cod_SIAPE_unidade_exercicio"]
            == original_pt["cod_SIAPE_unidade_exercicio"]
        )
        # se são participantes diferentes, não há problema em haver
        # sobreposição
        and (input_pt["cpf_participante"] == original_pt["cpf_participante"])
        # se algum dos planos estiver cancelado, não há problema em haver
        # sobreposição
        and any((plano.get("cancelado", False) for plano in (input_pt, original_pt)))
    ):
        if (
            date(input_pt["data_inicio_plano"])
            < date(original_pt["data_termino_plano"])
        ) and (
            date(input_pt["data_termino_plano"])
            > date(original_pt["data_inicio_plano"])
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "Já existe um plano de trabalho para este "
                "cod_SIAPE_unidade_exercicio para este cpf_participante "
                "no período informado."
            )
            assert response.json().get("detail", None) == detail_msg
            return

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == input_pt


@pytest.mark.parametrize(
    "data_inicio_plano, data_termino_plano",
    [
        ("2023-01-01", "2023-06-30"),  # igual ao exemplo
        ("2023-01-01", "2024-01-01"),  # um ano
        ("2023-01-01", "2024-01-02"),  # mais que um ano
    ],
)
def test_create_plano_trabalho_date_interval_over_a_year(
    truncate_pt,  # pylint: disable=unused-argument
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
        f"/plano_entregas/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if date.fromisoformat(data_termino_plano) - date.fromisoformat(
        data_inicio_plano
    ) > timedelta(days=366):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = "Plano de trabalho não pode abranger período maior que " "1 ano."
        assert response.json().get("detail", None) == detail_msg
    else:
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == input_pt


def test_create_pt_cod_plano_inconsistent(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
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
        "Parâmetro id_plano_trabalho_participante na URL e no JSON devem ser iguais"
    )
    assert response.json().get("detail", None) == detail_msg


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
        f"/plano_trabalho/{input_pt['id_plano_entrega_unidade']}",
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
        detail_msg = (
            "Data fim do Plano de Trabalho deve ser maior"
            " ou igual que Data de início."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
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
        data_inicio_registro < data_inicio_plano
        or data_fim_registro > data_termino_plano
    ):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = (
            "Data de início e de fim de registro devem ser maiores ou iguais"
            " que a Data de início do Plano de Trabalho."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_trabalho_participante, consolidacoes",
    [
        (101, [("2023-01-01", "2023-02-01")]),  # igual ao exemplo
        (
            102,
            [("2023-01-01", "2023-01-14"), ("2023-01-15", "2023-01-31")],
        ),  # sem sobreposição
        (
            103,
            [("2023-01-01", "2023-01-14"), ("2022-12-16", "2023-01-01")],
        ),  # sobreposição no início
        (
            104,
            [("2023-01-01", "2023-01-14"), ("2023-01-14", "2023-01-31")],
        ),  # sobreposição no fim
        (
            105,
            [
                ("2023-01-01", "2023-01-14"),
                ("2023-01-14", "2023-01-31"),
                ("2023-01-31", "2023-02-14"),
            ],
        ),  # sobreposições múltiplas
        (
            106,
            [("2023-01-01", "2023-01-14"), ("2023-01-02", "2023-01-13")],
        ),  # contido no período
        (
            107,
            [("2023-01-01", "2023-01-14"), ("2022-12-31", "2023-01-15")],
        ),  # contém o período
        (
            108,
            [("2023-01-01", "2023-01-14"), ("2023-01-14", "2023-01-31")],
        ),  # outra unidade
        (
            109,
            [("2023-01-01", "2023-01-14"), ("2023-01-14", "2023-01-31")],
        ),  # outro participante
        (
            110,
            [("2023-01-01", "2023-01-14"), ("2023-01-14", "2023-01-31")],
        ),  # ambos diferentes
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

    for consolidacao_1, consolidacao_2 in zip(consolidacoes[:-1], consolidacoes[1:]):
        print("consolidacao_1: ", consolidacao_1)
        print("consolidacao_2: ", consolidacao_2)
        data_fim_registro_1 = date.fromisoformat(consolidacao_1[1])
        data_inicio_registro_2 = date.fromisoformat(consolidacao_2[0])
        if data_inicio_registro_2 < data_fim_registro_1:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "Uma ou mais consolidações possuem data_inicio_registro e "
                "data_fim_registro sobrepostas."
            )
            assert response.json().get("detail", None) == detail_msg
            return

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == input_pt


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
        detail_msg = "Tipo de contribuição inválida; permitido: 1 a 3"
        assert response.json().get("detail") == detail_msg


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
            detail_msg = (
                "É necessário informar id_entrega quando tipo_contribuicao == 1"
            )
            assert response.json().get("detail")[0]["msg"] == detail_msg
        elif (
            id_plano_entrega_unidade != id_plano_entrega_existente
            or id_entrega not in ids_entregas_existentes
        ):
            # TODO: Verificar impacto no desempenho com grande volume de requisições
            # e se pode ser aproveitada a verificação de FK no banco
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = "Referência a id_entrega não encontrada"
            assert response.json().get("detail")[0]["msg"] == detail_msg
    elif tipo_contribuicao == 2 and id_entrega:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = "Não se deve informar id_entrega quando tipo_contribuicao == 2"
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_201_CREATED


def test_create_pt_duplicate_id_plano(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/555",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/555",
        json=input_pt,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) is None
    assert response.json() == input_pt


@pytest.mark.parametrize("horas_vinculadas", [-2, -1])
def test_create_pt_invalid_horas_vinculadas(
    input_pt: dict,
    horas_vinculadas: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    id_plano_trabalho_participante = "138"
    input_pt["id_plano_trabalho_participante"] = id_plano_trabalho_participante
    input_pt["horas_vinculadas"] = horas_vinculadas
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_trabalho/{id_plano_trabalho_participante}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Valor de horas_vinculadas deve ser maior ou igual a zero"
    assert response.json().get("detail")[0]["msg"] == detail_msg


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
        detail_msg = "Avaliação de plano de trabalho inválida; permitido: 1 a 5"
        assert response.json().get("detail") == detail_msg


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
    detail_msg = [
        "Value error, Dígitos verificadores do CPF inválidos.",
        "Value error, CPF inválido.",
        "Value error, CPF precisa ter 11 dígitos.",
        "Value error, CPF deve conter apenas dígitos.",
    ]
    assert response.json().get("detail")[0]["msg"] in detail_msg
