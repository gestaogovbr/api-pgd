"""Testes relacionados a verificações de datas associadas ao Plano de
Trabalho.
"""

from datetime import date

from fastapi import status

import pytest

from util import over_a_year, assert_error_message
from .core_test import BasePTTest


# Datas básicas


class TestCreatePTInvalidDates(BasePTTest):
    """Testes relacionados a criar um Plano de Trabalho com datas inválidas."""

    @pytest.mark.parametrize(
        "id_plano_trabalho, data_assinatura_tcr, data_inicio, data_termino",
        [
            ("77", "2023-03-01", "2023-04-01", "2023-06-04"),  # OK
            ("78", "2023-03-01", "2023-06-04", "2023-04-01"),  # término antes do início
            ("79", "2023-06-01", "2023-04-01", "2023-06-04"),  # início antes do TCR
        ],
    )
    def test_create_pt_invalid_dates(
        self,
        input_part: dict,
        id_plano_trabalho: str,
        data_assinatura_tcr: str,
        data_inicio: str,
        data_termino: str,
    ):
        """Verifica se a data_termino_plano é maior ou igual à data_inicio_plano."""
        input_part["data_assinatura_tcr"] = data_assinatura_tcr
        input_pt = self.input_pt.copy()
        input_pt["data_inicio"] = data_inicio
        input_pt["data_termino"] = data_termino
        input_pt["id_plano_trabalho"] = id_plano_trabalho

        # cria o participante com a data_assinatura_tcr informada
        response = self.client.put(
            (
                "/organizacao/SIAPE"
                f"/{input_part['cod_unidade_autorizadora']}"
                f"/{input_part['cod_unidade_lotacao']}"
                f"/participante/{input_part['matricula_siape']}"
            ),
            json=input_part,
            headers=self.header_usr_1,
        )
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)

        # cria o plano_trabalho com a data_inicio informada
        response = self.create_pt(input_pt)
        if date.fromisoformat(data_inicio) > date.fromisoformat(data_termino):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "data_termino do Plano de Trabalho deve ser maior ou igual que data_inicio"
            assert_error_message(response, detail_message)
        else:
            assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        "data_inicio_pt",
        (
            "2022-12-01", # anterior à data_inicio do pe, que é "2023-01-01"
            "2023-01-15",
        ),
    )
    def test_data_inicio_check(
        self,
        input_pe: dict,
        data_inicio_pt: str,
    ):
        """Testa a criação de um Plano de Trabalho com diferentes datas de
        início. Caso a data de início do Plano de Trabalho seja anterior
        à data de início do Plano de Entregas, deverá recusar a entrada
        com uma mensagem de erro.

        Args:
            input_pe (dict): Dados do PE usado como exemplo.
            data_inicio_pt (str): Data recebida como parâmetro de teste.
        """
        # Atualiza a data de início do Plano de Trabalho
        input_pt = self.input_pt.copy()
        input_pt["data_inicio"] = data_inicio_pt

        response = self.create_pt(input_pt, header_usr=self.header_usr_1)

        if date.fromisoformat(data_inicio_pt) < date.fromisoformat(
            input_pe["data_inicio"]
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert_error_message(
                response,
                "A data de início do Plano de Trabalho não pode ser anterior "
                "à data de início do Plano de Entregas.",
            )
        else:
            assert response.status_code == status.HTTP_201_CREATED


class TestCreatePTDateIntervalOverAYear(BasePTTest):
    """Testes relacionados a criar um Plano de Trabalho com intervalo de
    data superior a um ano."""

    @pytest.mark.parametrize(
        "data_inicio, data_termino",
        [
            ("2023-01-01", "2023-06-30"),  # igual ao exemplo
            ("2023-01-01", "2024-01-01"),  # um ano
            ("2023-01-01", "2024-01-02"),  # mais que um ano
        ],
    )
    def test_create_plano_trabalho_date_interval_over_a_year(
        self, data_inicio: str, data_termino: str
    ):
        """Plano de Entregas não pode ter vigência superior a um ano."""
        input_pt = self.input_pt.copy()
        input_pt["data_inicio"] = data_inicio
        input_pt["data_termino"] = data_termino

        response = self.create_pt(input_pt)

        if (
            over_a_year(
                date.fromisoformat(data_termino), date.fromisoformat(data_inicio)
            )
            == 1
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "Plano de trabalho não pode abranger período maior que 1 ano."
            )
            assert_error_message(response, detail_message)
        else:
            assert response.status_code == status.HTTP_201_CREATED
            self.assert_equal_plano_trabalho(response.json(), input_pt)


class TestCreatePTOverlappingDateInterval(BasePTTest):
    """Testes relacionados a criar um Plano de Trabalho com sobreposição
    de intervalo de data na mesma unidade para o mesmo participante."""

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
            (
                "108",
                100,
                "64635210600",
                "2023-01-01",
                "2023-01-15",
                False,
            ),  # outra unidade
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
        self,
        id_plano_trabalho: str,
        cod_unidade_executora: int,
        cpf_participante: str,
        data_inicio: str,
        data_termino: str,
        cancelado: bool,
    ):
        """Tenta criar um plano de trabalho com sobreposição de intervalo de
        data na mesma unidade para o mesmo participante.

        O Plano de Trabalho original é criado e então é testada a criação de
        cada novo Plano de Trabalho, com sobreposição ou não das datas, sendo
        da mesma ou outra unidade, de mesmo ou outro participante, conforme
        especificado nos parâmetros de teste.
        """
        input_pt = self.input_pt.copy()
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
        response = self.create_pt(input_pt2)

        assert response.status_code == status.HTTP_201_CREATED

        input_pt["id_plano_trabalho"] = id_plano_trabalho
        input_pt["cod_unidade_executora"] = cod_unidade_executora
        input_pt["cpf_participante"] = cpf_participante
        input_pt["data_inicio"] = data_inicio
        input_pt["data_termino"] = data_termino
        input_pt["cancelado"] = cancelado
        input_pt["avaliacao_registros_execucao"] = []
        response = self.create_pt(input_pt)

        if (
            # se algum dos planos estiver cancelado, não há problema em haver
            # sobreposição
            not cancelado
            # se são unidades diferentes, não há problema em haver sobreposição
            and (
                input_pt["cod_unidade_executora"]
                == original_pt["cod_unidade_executora"]
            )
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
                assert_error_message(response, detail_msg)
            else:
                # não há sobreposição de datas
                assert response.status_code == status.HTTP_201_CREATED
                self.assert_equal_plano_trabalho(response.json(), input_pt)
        else:
            # um dos planos está cancelado, deve ser criado
            assert response.status_code == status.HTTP_201_CREATED
            self.assert_equal_plano_trabalho(response.json(), input_pt)


# Datas de avaliação


class TestCreatePTDataAvaliacao(BasePTTest):
    """Testes relacionados a criar um Plano de Trabalho com datas de
    avaliação fora do intervalo do Plano de Trabalho."""

    @pytest.mark.parametrize(
        "id_plano_trabalho, data_inicio, data_termino, "
        "data_inicio_periodo_avaliativo, data_fim_periodo_avaliativo",
        [
            ("80", "2023-06-04", "2023-06-11", "2023-04-01", "2023-04-02"),
            ("81", "2023-06-04", "2023-06-11", "2024-04-01", "2023-04-02"),
            ("82", "2023-06-04", "2023-06-11", "2021-04-02", "2023-06-02"),
            ("83", "2023-04-01", "2023-04-01", "2023-06-01", "2023-06-02"),
            ("84", "2023-04-01", "2023-04-01", "2023-04-01", "2023-04-01"),
        ],
    )
    def test_create_pt_data_avaliacao_out_of_bounds(
        self,
        id_plano_trabalho: str,
        data_inicio: str,
        data_termino: str,
        data_inicio_periodo_avaliativo: str,
        data_fim_periodo_avaliativo: str,
    ):
        """Verifica se o período de avaliação do registro de execução está
        dentro do intervalo do Plano de Trabalho.
        """
        input_pt = self.input_pt.copy()
        input_pt["id_plano_trabalho"] = id_plano_trabalho
        input_pt["data_inicio"] = data_inicio
        input_pt["data_termino"] = data_termino
        input_pt["avaliacao_registros_execucao"][0][
            "data_inicio_periodo_avaliativo"
        ] = data_inicio_periodo_avaliativo
        input_pt["avaliacao_registros_execucao"][0][
            "data_fim_periodo_avaliativo"
        ] = data_fim_periodo_avaliativo

        response = self.create_pt(input_pt)
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


class TestCreatePlanoDeTrabalhoPeriodoAvaliativoOverlapping(BasePTTest):
    """Testes para a criação de Plano de Trabalho com sobreposição de
    período avaliativo.

    Essa classe testa a criação de Plano de Trabalho com diferentes
    cenários de sobreposição de período avaliativo, verificando se a
    API rejeita corretamente os casos de sobreposição.
    """

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
        self, id_plano_trabalho: int, periodo_avaliativo: list[tuple[str, str]]
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
        original_avaliacao = self.input_pt["avaliacao_registros_execucao"][0].copy()

        input_pt = self.input_pt.copy()
        input_pt["id_plano_trabalho"] = id_plano_trabalho

        input_pt["avaliacao_registros_execucao"] = []
        for avaliacao in periodo_avaliativo:
            avaliacao_template = original_avaliacao.copy()
            avaliacao_template["data_inicio_periodo_avaliativo"] = avaliacao[0]
            avaliacao_template["data_fim_periodo_avaliativo"] = avaliacao[1]
            input_pt["avaliacao_registros_execucao"].append(avaliacao_template)

        response = self.create_pt(input_pt)

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
                    "data_inicio_periodo_avaliativo e data_fim_periodo_avaliativo "
                    "sobrepostas."
                )
                assert_error_message(response, detail_message)
                return

        assert response.status_code == status.HTTP_201_CREATED
        self.assert_equal_plano_trabalho(response.json(), input_pt)
