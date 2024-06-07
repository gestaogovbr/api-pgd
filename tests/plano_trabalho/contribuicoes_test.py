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
        input_pt["contribuicoes"][0]["percentual_contribuicao"] = percentual_contribuicao

        response = self.create_pt(input_pt)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreatePTInvalidTipoContribuicao(BasePTTest):
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
            detail_message = "Tipo de contribuição inválida; permitido: 1 a 3"
            assert_error_message(response, detail_message)


class TestPercentualContribuicao(BasePTTest):
    """Testes para verificar a validação do percentual de contribuição no
    Plano de Trabalho."""

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

    @pytest.mark.parametrize("omitted_fields", enumerate(FIELDS_CONTRIBUICAO["optional"]))
    def test_create_plano_trabalho_contribuicao_omit_optional_fields(
        self,
        omitted_fields: list,
    ):
        """Tenta criar um novo plano de trabalho omitindo campos opcionais"""
        partial_input_pt = self.input_pt.copy()
        offset, field_list = omitted_fields
        for field in field_list:
            for contribuicao in partial_input_pt["contribuicoes"]:
                if field in contribuicao:
                    del contribuicao[field]

        partial_input_pt["id_plano_trabalho"] = 557 + offset
        response = self.create_pt(partial_input_pt)
        assert response.status_code == status.HTTP_201_CREATED


class TestCreatePTNullOptionalFields(BasePTTest):
    """Testa a criação de um novo Plano de Trabalho enviando null nos
    campos opcionais da contribuição.

    Verifica se o endpoint de criação de Plano de Trabalho aceita a
    requisição quando campos opcionais da contribuição são enviados com
    valor null.
    """

    @pytest.mark.parametrize("nulled_fields", enumerate(FIELDS_CONTRIBUICAO["optional"]))
    def test_create_plano_trabalho_contribuicao_null_optional_fields(
        self,
        nulled_fields: list,
    ):
        """Tenta criar um novo plano de trabalho enviando null nos campos opcionais"""
        partial_input_pt = self.input_pt.copy()
        offset, field_list = nulled_fields
        for field in field_list:
            for contribuicao in partial_input_pt["contribuicoes"]:
                if field in contribuicao:
                    contribuicao[field] = None

        partial_input_pt["id_plano_trabalho"] = 557 + offset
        response = self.create_pt(partial_input_pt)
        assert response.status_code == status.HTTP_201_CREATED
