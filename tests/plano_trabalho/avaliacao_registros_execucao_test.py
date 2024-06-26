"""Testes para validar a Avaliação de registros de execução do
Plano de Trabalho.
"""

from datetime import date

import pytest
from fastapi import status

from util import assert_error_message

from .core_test import BasePTTest, FIELDS_AVALIACAO_REGISTROS_EXECUCAO


class TestCreatePTMissingMandatoryFieldsAvaliacaoRegistrosExecucao(BasePTTest):
    """Testes para verificar a rejeição da criação de Plano de Trabalho
    quando campos obrigatórios da avaliação de registros de execução
    estão faltando.
    """

    @pytest.mark.parametrize(
        "omitted_fields", enumerate(FIELDS_AVALIACAO_REGISTROS_EXECUCAO["mandatory"])
    )
    def test_create_pt_missing_mandatory_fields_avaliacao_registros_execucao(
        self,
        omitted_fields: list,
    ):
        """
        Verifica se o endpoint de criação de Plano de Trabalho rejeita a
        requisição quando algum campo obrigatório da avaliação de
        registros de execução está faltando.
        """
        input_pt = self.input_pt.copy()
        _, field_list = omitted_fields
        for field in field_list:
            input_pt["avaliacoes_registros_execucao"][0][field] = None

        input_pt["id_plano_trabalho"] = "111222333"
        response = self.create_pt(input_pt)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreatePTInvalidAvaliacaoRegistrosExecucao(BasePTTest):
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

    @pytest.mark.parametrize("avaliacao_registros_execucao", [0, 1, 2, 5, 6])
    def test_create_pt_invalid_avaliacao_registros_execucao(
        self,
        avaliacao_registros_execucao: int,
    ):
        """Testa a criação de um plano de trabalho com um valor inválido para
        o campo avaliacao_registros_execucao.
        """
        input_pt = self.input_pt.copy()
        input_pt["avaliacoes_registros_execucao"][0]["id_periodo_avaliativo"] = str(
            10 + avaliacao_registros_execucao
        )
        input_pt["avaliacoes_registros_execucao"][0][
            "avaliacao_registros_execucao"
        ] = avaliacao_registros_execucao

        response = self.create_pt(input_pt)

        if avaliacao_registros_execucao in range(1, 6):
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "Avaliação de registros de execução inválida; permitido: 1 a 5"
            )
            assert_error_message(response, detail_message)


class TestCreatePTInvalidAvaliacaoRegistrosExecucaoDates(BasePTTest):
    """Testa a criação de um plano de trabalho com datas inválidas para
    o período avaliativo na avaliação de registros de execução.

    O teste envia uma requisição PUT para a rota
    "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
    com diferentes combinações de datas para o período avaliativo e para
    o início do Plano de Trabalho.

    Quando as datas são válidas (data_fim_periodo_avaliativo >=
    data_inicio_periodo_avaliativo e data_inicio_periodo_avaliativo >
    data_inicio_plano_trabalho), espera-se que a resposta tenha o status
    HTTP 201 Created. Quando as datas são inválidas, espera-se que a
    resposta tenha o status HTTP 422 Unprocessable Entity e que a
    mensagem de erro apropriada esteja presente na resposta.
    """

    # TODO: Verificar com área de negócio se essa validação é assim mesmo
    # @pytest.mark.parametrize(
    #     "data_inicio_periodo_avaliativo, data_fim_periodo_avaliativo",
    #     [
    #         ("2023-01-01", "2022-12-31"),
    #         ("2023-01-01", "2023-01-01"),
    #         ("2023-01-01", "2023-01-02"),
    #     ],
    # )
    # def test_create_pt_invalid_avaliacao_registros_execucao_dates(
    #     self,
    #     data_inicio_periodo_avaliativo: str,
    #     data_fim_periodo_avaliativo: str,
    # ):
    #     """Testa a criação de um plano de trabalho com datas inválidas para
    #     o período avaliativo na avaliação de registros de execução.

    #     Args:
    #         data_inicio_periodo_avaliativo (str): Data de início do período avaliativo.
    #         data_fim_periodo_avaliativo (str): Data de fim do período avaliativo.
    #     """
    #     input_pt = self.input_pt.copy()
    #     input_pt["avaliacoes_registros_execucao"][0][
    #         "data_inicio_periodo_avaliativo"
    #     ] = data_inicio_periodo_avaliativo
    #     input_pt["avaliacoes_registros_execucao"][0][
    #         "data_fim_periodo_avaliativo"
    #     ] = data_fim_periodo_avaliativo

    #     response = self.create_pt(input_pt)

    #     if date.fromisoformat(data_fim_periodo_avaliativo) >= date.fromisoformat(
    #         data_inicio_periodo_avaliativo
    #     ):
    #         assert response.status_code == status.HTTP_201_CREATED
    #     else:
    #         assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    #         detail_message = (
    #             "A data de fim do período avaliativo deve ser igual ou "
    #             "posterior à data de início"
    #         )
    #         assert_error_message(response, detail_message)

    @pytest.mark.parametrize(
        "data_inicio_plano_trabalho, data_inicio_periodo_avaliativo",
        [
            ("2023-01-01", "2022-12-31"),
            ("2023-01-01", "2023-01-01"),
            ("2023-01-01", "2023-01-02"),
        ],
    )
    def test_create_pt_invalid_avaliacao_registros_execucao_start_date(
        self,
        data_inicio_plano_trabalho: str,
        data_inicio_periodo_avaliativo: str,
    ):
        """Testa a criação de um plano de trabalho com a data de início do
        período avaliativo anterior, igual ou posterior à data de início do
        Plano de Trabalho.

        Aqueles que possuem data de início do período avaliativo anterior à
        data de início do Plano de Trabalho devem ser rejeitados.
        """
        input_pt = self.input_pt.copy()
        input_pt["data_inicio_plano_trabalho"] = data_inicio_plano_trabalho
        input_pt["avaliacoes_registros_execucao"][0][
            "data_inicio_periodo_avaliativo"
        ] = data_inicio_periodo_avaliativo

        response = self.create_pt(input_pt)

        if date.fromisoformat(data_inicio_periodo_avaliativo) > date.fromisoformat(
            data_inicio_plano_trabalho
        ):
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "A data de início do período avaliativo deve ser posterior "
                "à data de início do Plano de Trabalho"
            )
            assert_error_message(response, detail_message)

    @pytest.mark.parametrize(
        "data_inicio_periodo_avaliativo, data_avaliacao_registros_execucao",
        [
            ("2023-01-01", "2022-12-31"),
            ("2023-01-01", "2023-01-01"),
            ("2023-01-01", "2023-01-02"),
        ],
    )
    def test_create_pt_invalid_avaliacao_registros_execucao_date(
        self,
        data_inicio_periodo_avaliativo: str,
        data_avaliacao_registros_execucao: str,
    ):
        """Testa a criação de um plano de trabalho com a data de avaliação
        de registros de execução anterior à data de início do período
        avaliativo.
        """
        input_pt = self.input_pt.copy()
        input_pt["avaliacoes_registros_execucao"][0][
            "data_inicio_periodo_avaliativo"
        ] = data_inicio_periodo_avaliativo
        input_pt["avaliacoes_registros_execucao"][0][
            "data_avaliacao_registros_execucao"
        ] = data_avaliacao_registros_execucao

        response = self.create_pt(input_pt)

        if date.fromisoformat(data_avaliacao_registros_execucao) > date.fromisoformat(
            data_inicio_periodo_avaliativo
        ):
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "A data de avaliação de registros de execução "
                "deve ser posterior à data de início do período avaliativo"
            )
            assert_error_message(response, detail_message)
