"""Testes relacionados a verificações de datas associadas ao Plano de
Trabalho.
"""

from datetime import date

from httpx import Client
from fastapi import status

import pytest

from util import over_a_year, assert_error_message
from .core_test import assert_equal_plano_trabalho


# Datas básicas


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


# Datas de avaliação


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