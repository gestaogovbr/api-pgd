"""Testes para validar a Avaliação de registros de execução do
Plano de Trabalho.
"""

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
        response = self.put_plano_trabalho(input_pt)
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

        response = self.put_plano_trabalho(input_pt)

        if avaliacao_registros_execucao in range(1, 6):
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "Avaliação de registros de execução inválida; permitido: 1 a 5"
            )
            assert_error_message(response, detail_message)
