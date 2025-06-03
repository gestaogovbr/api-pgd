"""Testes relacionados a verificações de datas associadas ao Plano de
Trabalho.
"""

from copy import deepcopy
from datetime import date, timedelta

from fastapi import status

import pytest

from util import over_a_year, assert_error_message
from .core_test import BasePTTest

# Datas básicas


class TestCreatePTInvalidDates(BasePTTest):
    """Testes relacionados a criar um Plano de Trabalho com datas inválidas."""

    @pytest.mark.parametrize(
        ("data_inicio, data_termino"),
        [
            # data_inicio posterior à data_termino (inválida)
            (date(2023, 7, 1), date(2023, 6, 1)),
        ],
    )
    def test_create_pt_invalid_dates(
        self,
        example_part: dict,  # pylint: disable=unused-argument
        input_part: dict,
        data_inicio: date,
        data_termino: date,
    ):
        """Testa a criação de um plano de trabalho com datas de início
        que violam certas regras de validação.
        """
        input_pt = deepcopy(self.input_pt)
        # evitar validações sem relação com o teste
        input_pt["avaliacoes_registros_execucao"] = []
        input_pt["data_inicio"] = data_inicio.isoformat()
        input_pt["data_termino"] = data_termino.isoformat()

        response = self.put_plano_trabalho(input_pt)

        if data_inicio > data_termino:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "data_termino do Plano de Trabalho deve ser maior ou igual "
                "que data_inicio"
            )
            assert_error_message(response, detail_message)
        else:
            assert response.status_code == status.HTTP_201_CREATED


class TestCreatePTDateIntervalOverAYear(BasePTTest):
    """Testes relacionados a criar um Plano de Trabalho com intervalo de
    data superior a um ano."""

    @pytest.mark.parametrize(
        "data_inicio, data_termino",
        [
            ("2023-06-01", "2023-06-30"),  # igual ao exemplo
            ("2023-06-01", "2024-06-01"),  # um ano
            ("2023-06-01", "2024-06-02"),  # mais que um ano
        ],
    )
    def test_create_plano_trabalho_date_interval_over_a_year(
        self, data_inicio: str, data_termino: str
    ):
        """Plano de trabalho não pode ter vigência superior a um ano."""
        input_pt = deepcopy(self.input_pt)
        input_pt["data_inicio"] = data_inicio
        input_pt["data_termino"] = data_termino

        response = self.put_plano_trabalho(input_pt)

        if (
            over_a_year(
                date.fromisoformat(data_inicio), date.fromisoformat(data_termino)
            )
            == 1
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "Plano de trabalho não pode abranger período maior que 1 ano"
            )
            assert_error_message(response, detail_message)
        else:
            assert response.status_code == status.HTTP_201_CREATED
            self.assert_equal_plano_trabalho(response.json(), input_pt)


class TestCreatePTOverlappingDateInterval(BasePTTest):
    """Testes relacionados a criar um Plano de Trabalho com sobreposição
    de intervalo de data na mesma unidade para o mesmo participante."""

    @pytest.mark.parametrize(
        "id_plano_trabalho, cod_unidade_executora, matricula_siape, "
        "data_inicio, data_termino, "
        "status_pt",
        [
            (
                "101",
                99,
                "1237654",
                "2023-06-08",
                "2023-06-15",
                2,
            ),  # igual ao exemplo
            (
                "102",
                99,
                "1237654",
                "2023-07-01",
                "2023-07-15",
                2,
            ),  # sem sobreposição
            # sobreposição no início
            ("103", 99, "1237654", "2023-06-01", "2023-06-08", 2),
            # sobreposição no fim
            ("104", 99, "1237654", "2023-06-15", "2023-07-15", 2),
            (
                "105",
                99,
                "1237654",
                "2023-06-09",
                "2023-06-10",
                2,
            ),  # contido no período
            (
                "106",
                99,
                "1237654",
                "2023-06-07",
                "2023-06-16",
                2,
            ),  # contém o período
            ("107", 99, "1237654", "2023-06-01", "2023-06-30", 1),  # cancelado
            (
                "109",
                100,
                "1234567",
                "2023-06-01",
                "2023-06-15",
                2,
            ),  # outro participante
        ],
    )
    def test_create_plano_trabalho_overlapping_date_interval(
        self,
        id_plano_trabalho: str,
        cod_unidade_executora: int,
        matricula_siape: str,
        data_inicio: str,
        data_termino: str,
        status_pt: int,
        example_pt,
        example_part_lotacao_99,
    ):
        """Tenta criar um plano de trabalho com sobreposição de intervalo de
        data na mesma unidade para o mesmo participante.

        O Plano de Trabalho original é criado e então é testada a criação de
        cada novo Plano de Trabalho, com sobreposição ou não das datas, sendo
        da mesma ou outra unidade, de mesmo ou outro participante, conforme
        especificado nos parâmetros de teste.
        """
        input_pt = deepcopy(self.input_pt)
        input_pt["data_inicio"] = "2023-06-08"
        original_pt = input_pt.copy()
        input_pt2 = original_pt.copy()
        input_pt2["id_plano_trabalho"] = "556"
        input_pt2["data_inicio"] = "2023-06-16"
        input_pt2["data_termino"] = "2023-06-30"
        input_pt2["avaliacoes_registros_execucao"] = [
            {
                "id_periodo_avaliativo": "string",
                "data_inicio_periodo_avaliativo": "2023-06-16",
                "data_fim_periodo_avaliativo": "2023-06-23",
                "avaliacao_registros_execucao": 5,
                "data_avaliacao_registros_execucao": "2023-06-23",
                "matricula_siape": "1237654",
                "carga_horaria_disponivel": 80,
            }
        ]
        response = self.put_plano_trabalho(input_pt2)
        assert response.status_code == status.HTTP_201_CREATED

        input_pt["id_plano_trabalho"] = id_plano_trabalho
        input_pt["cod_unidade_executora"] = cod_unidade_executora
        input_pt["matricula_siape"] = matricula_siape
        input_pt["data_inicio"] = data_inicio
        input_pt["data_termino"] = data_termino
        input_pt["status"] = status_pt
        input_pt["avaliacoes_registros_execucao"] = []
        response = self.put_plano_trabalho(input_pt)

        if (
            # se algum dos planos estiver cancelado, não há problema em haver
            # sobreposição
            status_pt != 1
            # se são unidades diferentes, não há problema em haver sobreposição
            and (
                input_pt["cod_unidade_executora"]
                == original_pt["cod_unidade_executora"]
            )
            # se são participantes diferentes, não há problema em haver
            # sobreposição
            and (input_pt["matricula_siape"] == original_pt["matricula_siape"])
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
                    "cod_unidade_executora para esta matrícula "
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
        "id_plano_trabalho, data_inicio_periodo_avaliativo, "
        "data_fim_periodo_avaliativo",
        [
            # período inteiro antes da data_inicio do Plano de Trabalho
            ("80", "2023-06-01", "2023-06-07"),
            # fim antes do início
            ("81", "2023-06-11", "2022-06-10"),
            # início igual à data_inicio do Plano de Trabalho
            ("82", "2023-06-08", "2023-06-09"),
        ],
    )
    def test_create_pt_invalid_periodo_avaliativo(
        self,
        id_plano_trabalho: str,
        data_inicio_periodo_avaliativo: str,
        data_fim_periodo_avaliativo: str,
    ):
        """Verifica se o período de avaliação do registro de execução:

        - começa antes de terminar
        - começa, no mínio, na data de início do Plano de Trabalho.
        """
        input_pt = deepcopy(self.input_pt)
        input_pt["data_inicio"] = "2023-06-08"
        input_pt["id_plano_trabalho"] = id_plano_trabalho
        input_pt["avaliacoes_registros_execucao"][0][
            "data_inicio_periodo_avaliativo"
        ] = data_inicio_periodo_avaliativo
        input_pt["avaliacoes_registros_execucao"][0]["data_fim_periodo_avaliativo"] = (
            data_fim_periodo_avaliativo
        )

        response = self.put_plano_trabalho(input_pt)

        if date.fromisoformat(data_fim_periodo_avaliativo) < date.fromisoformat(
            data_inicio_periodo_avaliativo
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "A data de fim do período avaliativo deve ser igual ou "
                "posterior à data de início do período avaliativo."
            )
            assert_error_message(response, detail_message)
        elif date.fromisoformat(data_inicio_periodo_avaliativo) < date.fromisoformat(
            input_pt["data_inicio"]
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "A data de início do período avaliativo deve ser igual ou "
                "posterior à data de início do Plano de Trabalho."
            )
            assert_error_message(response, detail_message)
        else:
            assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        "data_avaliacao_registros_execucao",
        [
            "2099-01-01",  # data futura
            date.today().strftime("%Y-%m-%d"),  # data atual
            "2023-06-02",  # data passada
        ],
    )
    def test_create_pt_data_avaliacao_future_date(
        self,
        data_avaliacao_registros_execucao: str,
    ):
        """Verifica se a data de avaliação do registro de execução é
        inferior ou igual a data de envio.
        """
        input_pt = deepcopy(self.input_pt)
        input_pt["avaliacoes_registros_execucao"][0][
            "data_avaliacao_registros_execucao"
        ] = data_avaliacao_registros_execucao
        print (input_pt)
        response = self.put_plano_trabalho(input_pt)
        if date.fromisoformat(data_avaliacao_registros_execucao) > date.today():
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "A data de avaliação de registros de execução não pode ser "
                "superior à data atual."
            )
            assert_error_message(response, detail_message)
        else:
            assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        "id_plano_trabalho, data_inicio_periodo_avaliativo, "
        "data_fim_periodo_avaliativo, data_avaliacao_registros_execucao",
        [
            ("80", "2023-06-02", "2023-06-10", "2023-06-01"),  # antes do início
            ("81", "2023-06-01", "2023-06-10", "2023-06-01"),  # igual ao início
            ("82", "2023-06-01", "2023-06-10", "2023-06-05"),  # depois do início
            ("83", "2023-06-01", "2023-06-10", "2023-06-15"),  # depois do fim
        ],
    )
    def test_create_pt_data_avaliacao_out_of_bounds(
        self,
        id_plano_trabalho: str,
        data_inicio_periodo_avaliativo: str,
        data_fim_periodo_avaliativo: str,
        data_avaliacao_registros_execucao: str,
    ):
        """Verifica se a data de avaliação do registro de execução está
        dentro do período avaliativo.
        """
        input_pt = deepcopy(self.input_pt)
        input_pt["id_plano_trabalho"] = id_plano_trabalho
        input_pt["avaliacoes_registros_execucao"][0][
            "data_inicio_periodo_avaliativo"
        ] = data_inicio_periodo_avaliativo
        input_pt["avaliacoes_registros_execucao"][0][
            "data_fim_periodo_avaliativo"
        ] = data_fim_periodo_avaliativo
        input_pt["avaliacoes_registros_execucao"][0][
            "data_avaliacao_registros_execucao"
        ] = data_avaliacao_registros_execucao

        response = self.put_plano_trabalho(input_pt)
        if date.fromisoformat(data_avaliacao_registros_execucao) < date.fromisoformat(
            data_inicio_periodo_avaliativo
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "A data de avaliação de registros de execução deve ser igual ou "
                "posterior à data de início do período avaliativo."
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
            ("101", [("2023-06-01", "2023-06-02")]),  # igual ao exemplo
            (
                "102",
                [("2023-06-01", "2023-06-07"), ("2023-06-08", "2023-06-15")],
            ),  # sem sobreposição
            (
                "103",
                [("2023-06-07", "2023-06-15"), ("2023-06-01", "2023-06-07")],
            ),  # sobreposição no início
            (
                "104",
                [("2023-06-01", "2023-06-08"), ("2023-06-07", "2023-06-15")],
            ),  # sobreposição no fim
            (
                "105",
                [
                    ("2023-06-01", "2023-06-06"),
                    ("2023-06-06", "2023-06-11"),
                    ("2023-06-11", "2023-06-15"),
                ],
            ),  # sobreposições múltiplas
            (
                "106",
                [("2023-06-01", "2023-06-14"), ("2023-06-02", "2023-06-13")],
            ),  # contido no período
            (
                "107",
                [("2023-06-02", "2023-06-14"), ("2023-06-01", "2023-06-15")],
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
        original_avaliacao = self.input_pt["avaliacoes_registros_execucao"][0].copy()

        input_pt = deepcopy(self.input_pt)
        input_pt["id_plano_trabalho"] = id_plano_trabalho

        input_pt["avaliacoes_registros_execucao"] = []
        for number, avaliacao in enumerate(periodo_avaliativo):
            avaliacao_template = original_avaliacao.copy()
            avaliacao_template["id_periodo_avaliativo"] = f"{id_plano_trabalho}{number}"
            avaliacao_template["data_inicio_periodo_avaliativo"] = avaliacao[0]
            avaliacao_template["data_fim_periodo_avaliativo"] = avaliacao[1]
            avaliacao_template["data_avaliacao_registros_execucao"] = "2024-01-01"
            input_pt["avaliacoes_registros_execucao"].append(avaliacao_template)

        response = self.put_plano_trabalho(input_pt)

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
