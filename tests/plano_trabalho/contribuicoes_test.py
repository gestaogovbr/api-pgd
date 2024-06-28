"""Testes para validar uma Contribuição do Plano de Trabalho.
"""

from typing import Optional

import pytest

from fastapi import status

from util import assert_error_message

from .core_test import BasePTTest, FIELDS_CONTRIBUICAO

# Contribuições


class TestCreatePTMissingMandatoryFieldsContribuicoes(BasePTTest):
    """Testes para verificar a rejeição da criação de Plano de Trabalho
    quando campos obrigatórios da contribuição estão faltando.
    """

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
        self,
        tipo_contribuicao: int,
        percentual_contribuicao: int,
    ):
        """
        Verifica se o endpoint de criação de Plano de Trabalho rejeita a
        requisição quando algum campo obrigatório da contribuição está
        faltando.
        """
        input_pt = self.input_pt.copy()
        input_pt["id_plano_trabalho"] = "111222333"
        input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
        input_pt["contribuicoes"][0][
            "percentual_contribuicao"
        ] = percentual_contribuicao

        response = self.create_pt(input_pt)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreatePTInvalidTipoContribuicao(BasePTTest):
    """Testes para verificar a rejeição da criação de Plano de Trabalho
    quando uma de suas contribuições contém um campo tipo_contribuição
    com valor inválido.
    """

    @pytest.mark.parametrize(
        "tipo_contribuicao",
        [(-2), (0), (4)],
    )
    def test_create_pt_invalid_tipo_contribuicao(
        self,
        tipo_contribuicao: int,
    ):
        """
        Verifica se o endpoint de criação de Plano de Trabalho rejeita a
        requisição quando o tipo de contribuição é inválido.
        """
        input_pt = self.input_pt.copy()
        input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao

        response = self.create_pt(input_pt)

        if tipo_contribuicao in [1, 2, 3]:
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "Input should be 1, 2 or 3"
            assert_error_message(response, detail_message)


class TestPercentualContribuicao(BasePTTest):
    """Testes para verificar a validação do percentual de contribuição no
    Plano de Trabalho.
    """

    @pytest.mark.parametrize("percentual_contribuicao", [-10, 0, 50, 100, 110])
    def test_create_plano_trabalho_percentual_contribuicao(
        self,
        percentual_contribuicao: int,
    ):
        """Testa a criação de um Plano de Trabalho com diferentes valores
        de percentual de contribuição.

        Args:
            percentual_contribuicao (int): Valor do percentual de
                contribuição a ser testado.
        """
        input_pt = self.input_pt.copy()
        input_pt["contribuicoes"][0][
            "percentual_contribuicao"
        ] = percentual_contribuicao
        input_pt["contribuicoes"][1][
            "percentual_contribuicao"
        ] = percentual_contribuicao

        response = self.create_pt(input_pt, header_usr=self.header_usr_1)

        if 0 <= percentual_contribuicao <= 100:
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert_error_message(
                response, "O percentual de contribuição deve estar entre 0 e 100."
            )


class TestCreatePTOmitOptionalFields(BasePTTest):
    """Testa a criação de um novo Plano de Trabalho omitindo campos
    opcionais da contribuição.

    Verifica se o endpoint de criação de Plano de Trabalho aceita a
    requisição quando campos opcionais da contribuição são omitidos.
    """

    @pytest.mark.parametrize(
        "omitted_fields", enumerate(FIELDS_CONTRIBUICAO["optional"])
    )
    def test_create_plano_trabalho_contribuicao_omit_optional_fields(
        self,
        omitted_fields: list,
    ):
        """Tenta criar um novo plano de trabalho omitindo campos opcionais"""
        partial_input_pt = self.input_pt.copy()
        offset, field_list = omitted_fields
        for field in field_list:
            for contribuicao in partial_input_pt["contribuicoes"]:
                # torna os opcionais campos id_plano_entregas e id_entrega
                contribuicao["tipo_contribuicao"] = 3
                if field in contribuicao:
                    del contribuicao[field]

        partial_input_pt["id_plano_trabalho"] = str(557 + offset)
        response = self.create_pt(partial_input_pt)
        assert response.status_code == status.HTTP_201_CREATED


class TestCreatePTNullOptionalFields(BasePTTest):
    """Testa a criação de um novo Plano de Trabalho enviando null nos
    campos opcionais da contribuição.

    Verifica se o endpoint de criação de Plano de Trabalho aceita a
    requisição quando campos opcionais da contribuição são enviados com
    valor null.
    """

    @pytest.mark.parametrize(
        "nulled_fields", enumerate(FIELDS_CONTRIBUICAO["optional"])
    )
    def test_create_plano_trabalho_contribuicao_null_optional_fields(
        self,
        nulled_fields: list,
    ):
        """Tenta criar um novo plano de trabalho enviando null nos campos opcionais"""
        partial_input_pt = self.input_pt.copy()
        offset, field_list = nulled_fields
        for field in field_list:
            for contribuicao in partial_input_pt["contribuicoes"]:
                # torna os opcionais campos id_plano_entregas e id_entrega
                contribuicao["tipo_contribuicao"] = 3
                if field in contribuicao:
                    contribuicao[field] = None

        partial_input_pt["id_plano_trabalho"] = str(557 + offset)
        response = self.create_pt(partial_input_pt)
        assert response.status_code == status.HTTP_201_CREATED


class TestCreatePlanoTrabalhoContribuicoes(BasePTTest):
    """Testes relacionados às Contribuições ao criar um Plano de Trabalho."""

    @pytest.mark.parametrize(
        "tipo_contribuicao, id_plano_entregas, id_entrega",
        [
            (1, None, None),
            (1, "1", "1"),
            (1, "2", None),
            (2, None, None),
            (2, "1", None),
            (3, None, None),
            (3, "1", "1"),
        ],
    )
    def test_tipo_contribuicao(
        self,
        tipo_contribuicao: int,
        id_plano_entregas: Optional[str],
        id_entrega: Optional[str],
    ):
        """Testa a criação de um novo plano de trabalho, verificando as
        regras de validação para os campos relacionados à contribuição.

        O teste verifica as seguintes regras:

        1. Quando tipo_contribuicao == 1 (entrega da própria unidade),
           os campos id_plano_entregas e id_entrega são obrigatórios.
           Verifica também se a entrega referenciada existe.
        2. Quando tipo_contribuicao == 2 (não vinculada diretamente a entrega),
           os campos id_plano_entregas e id_entrega não devem ser informados.
        3. Quando tipo_contribuicao == 3 (entrega de outra unidade),
           os campos id_plano_entregas e id_entrega são opcionais.

        O teste envia uma requisição PUT para a rota
        "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
        com os dados de entrada atualizados de acordo com os parâmetros
        fornecidos. Verifica se a resposta possui o status HTTP correto (201
        Created ou 422 Unprocessable Entity) e se as mensagens de erro
        esperadas estão presentes na resposta.
        """
        input_pt = self.input_pt.copy()
        contribuicao = input_pt["contribuicoes"][0]
        contribuicao["tipo_contribuicao"] = tipo_contribuicao
        contribuicao["id_plano_entregas"] = id_plano_entregas
        contribuicao["id_entrega"] = id_entrega
        response = self.create_pt(input_pt, header_usr=self.header_usr_1)

        error_messages = []
        if tipo_contribuicao == 1:
            if id_plano_entregas is None or id_entrega is None:
                error_messages.append(
                    "Os campos id_plano_entregas e id_entrega são obrigatórios "
                    "quando tipo_contribuicao == 1."
                )
        if tipo_contribuicao == 2 and (id_plano_entregas or id_entrega):
            error_messages.append(
                "Os campos id_plano_entregas e id_entrega não podem conter "
                "valores quando tipo_contribuicao == 2. "
            )
        if error_messages:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            for detail_message in error_messages:
                assert_error_message(response, detail_message)
        else:
            assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        "id_entrega",
        ("1", "10"),
    )
    def test_referencia_entrega_inexistente(
        self,
        input_pe: dict,
        id_entrega: Optional[str],
    ):
        """Verifica se a referência feita à Entrega é uma entrega que existe,
        quando tipo_contribuicao==1. Se ela não existir, deve retornar erro.
        """
        input_pt = self.input_pt.copy()
        id_plano_entregas = "1"
        contribuicao = input_pt["contribuicoes"][0]
        contribuicao["tipo_contribuicao"] = 1
        contribuicao["id_plano_entregas"] = id_plano_entregas
        contribuicao["id_entrega"] = id_entrega

        response = self.create_pt(input_pt, header_usr=self.header_usr_1)

        if id_plano_entregas == input_pe["id_plano_entregas"] and \
            id_entrega in [entrega["id_entrega"] for entrega in input_pe["entregas"]]:
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert_error_message(
                response, "Contribuição do Plano de Trabalho faz referência a entrega inexistente"
            )
