"""Testes para validar uma Contribuição do Plano de Trabalho.
"""

from copy import deepcopy
from typing import Optional

import pytest

from fastapi import status

from util import assert_error_message

from .core_test import BasePTTest, FIELDS_CONTRIBUICAO

# Contribuições


class TestGetPTContribuicao(BasePTTest):
    """Testes para verificar os dados retornados ao consultar um
    Plano de Trabalho, em relação às suas contribuições.
    """

    def test_get_contribuicoes_sem_id(
        self,
        example_pt,  # pylint: disable=unused-argument
    ):
        """Verifica se as contribuições não estão aparecendo com o campo
        id, mas somente o campo id_contribuicao.
        """
        response = self.get_plano_trabalho(
            cod_unidade_autorizadora=self.input_pt["cod_unidade_autorizadora"],
            id_plano_trabalho=self.input_pt["id_plano_trabalho"],
        )
        assert response.status_code == status.HTTP_200_OK

        contribuicoes = response.json()["contribuicoes"]
        assert len(contribuicoes) > 0

        assert all(
            contribuicao.get("id", None) is None for contribuicao in contribuicoes
        )


class TestCreatePTContribuicaoMandatoryFields(BasePTTest):
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
        input_pt = deepcopy(self.input_pt)
        input_pt["id_plano_trabalho"] = "111222333"
        input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
        input_pt["contribuicoes"][0][
            "percentual_contribuicao"
        ] = percentual_contribuicao

        response = self.put_plano_trabalho(input_pt)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreatePTContribuicaoOptionalFields(BasePTTest):
    """Testa a criação de um novo Plano de Trabalho, em várias situações
    relacionadas aos campos opcionais da contribuição.

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
        partial_input_pt = deepcopy(self.input_pt)
        offset, field_list = omitted_fields
        for field in field_list:
            for contribuicao in partial_input_pt["contribuicoes"]:
                # torna os opcionais campos id_plano_entregas e id_entrega
                contribuicao["tipo_contribuicao"] = 3
                if field in contribuicao:
                    del contribuicao[field]

        partial_input_pt["id_plano_trabalho"] = str(557 + offset)
        response = self.put_plano_trabalho(partial_input_pt)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        "nulled_fields", enumerate(FIELDS_CONTRIBUICAO["optional"])
    )
    def test_create_plano_trabalho_contribuicao_null_optional_fields(
        self,
        nulled_fields: list,
    ):
        """Tenta criar um novo plano de trabalho enviando null nos campos opcionais"""
        partial_input_pt = deepcopy(self.input_pt)
        offset, field_list = nulled_fields
        for field in field_list:
            for contribuicao in partial_input_pt["contribuicoes"]:
                # torna os opcionais campos id_plano_entregas e id_entrega
                contribuicao["tipo_contribuicao"] = 3
                if field in contribuicao:
                    contribuicao[field] = None

        partial_input_pt["id_plano_trabalho"] = str(557 + offset)
        response = self.put_plano_trabalho(partial_input_pt)
        assert response.status_code == status.HTTP_201_CREATED


class TestCreatePTContribuicaoTipo(BasePTTest):
    """Testes para verificar, quando da criação de um Plano de Trabalho,
    diversas situações relacionadas ao campo tipo_contribuição.
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
        input_pt = deepcopy(self.input_pt)
        input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao

        response = self.put_plano_trabalho(input_pt)

        if tipo_contribuicao in [1, 2, 3]:
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "Input should be 1, 2 or 3"
            assert_error_message(response, detail_message)

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
        input_pt = deepcopy(self.input_pt)
        contribuicao = input_pt["contribuicoes"][0]
        contribuicao["tipo_contribuicao"] = tipo_contribuicao
        contribuicao["id_plano_entregas"] = id_plano_entregas
        contribuicao["id_entrega"] = id_entrega
        response = self.put_plano_trabalho(input_pt, header_usr=self.header_usr_1)

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


class TestCreatePTContribuicaoPercentual(BasePTTest):
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
        input_pt = deepcopy(self.input_pt)
        input_pt["contribuicoes"][0][
            "percentual_contribuicao"
        ] = percentual_contribuicao
        input_pt["contribuicoes"][1][
            "percentual_contribuicao"
        ] = percentual_contribuicao

        response = self.put_plano_trabalho(input_pt, header_usr=self.header_usr_1)

        if 0 <= percentual_contribuicao <= 100:
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert_error_message(
                response, "O percentual de contribuição deve estar entre 0 e 100."
            )


class TestCreatePTContribuicoesReferencias(BasePTTest):
    """Testes, quando da criação de um Plano de Trabalho, relacionados à
    verificação de referências das Contribuições a outras tabelas.
    """

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
        input_pt = deepcopy(self.input_pt)
        id_plano_entregas = "1"
        contribuicao = input_pt["contribuicoes"][0]
        contribuicao["tipo_contribuicao"] = 1
        contribuicao["id_plano_entregas"] = id_plano_entregas
        contribuicao["id_entrega"] = id_entrega

        response = self.put_plano_trabalho(input_pt, header_usr=self.header_usr_1)

        if id_plano_entregas == input_pe["id_plano_entregas"] and id_entrega in [
            entrega["id_entrega"] for entrega in input_pe["entregas"]
        ]:
            assert response.status_code == status.HTTP_201_CREATED
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert_error_message(
                response,
                "Contribuição do Plano de Trabalho faz referência a entrega inexistente",
            )

    def test_duplicate_id(self, example_pt):  # pylint: disable=unused-argument
        """Atualiza um Plano de Trabalho existente usando o método HTTP
        PUT, contendo ids duplicados na lista de contribuicoes.

        A chave opcional "id", existente até a versão 3.2.4, não deve ser
        informada; informá-la causa a recusa do envio, em caso de conflitos
        de id.

        O Pydantic, por padrão, ignora campos desconhecidos no schema.
        A partir da versão 3.2.5, o campo "id" foi retirado do schema e,
        por isso, é ignorado.

        O teste abaixo gera propositalmente um conflito no campo "id".
        """

        input_pt = deepcopy(self.input_pt)
        input_pt["contribuicoes"] = [
            {
                "id": 55501,
                "id_contribuicao": "55501",
                "tipo_contribuicao": 1,
                "id_plano_entregas": "1",
                "id_entrega": "1",
                "percentual_contribuicao": 40,
            },
            {
                "id": 55501,  # conflito com o id do item anterior
                "id_contribuicao": "55503",
                "tipo_contribuicao": 2,
                "id_plano_entregas": None,
                "id_entrega": None,
                "percentual_contribuicao": 30,
            },
            {
                "id": 55504,
                "id_contribuicao": "55504",
                "tipo_contribuicao": 1,
                "id_plano_entregas": "1",
                "id_entrega": "2",
                "percentual_contribuicao": 10,
            },
        ]

        response = self.put_plano_trabalho(input_pt)
        # o conflito no campo inexistente "id" deve ser ignorado
        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)

    def test_duplicate_id_contribuicao(
        self, example_pt
    ):  # pylint: disable=unused-argument
        """Atualiza um Plano de Trabalho existente usando o método HTTP
        PUT, contendo valores de id_contribuicao duplicados na lista de
        contribuicoes.
        """

        input_pt = deepcopy(self.input_pt)
        input_pt["contribuicoes"] = [
            {
                "id_contribuicao": "55501",
                "tipo_contribuicao": 1,
                "id_plano_entregas": "1",
                "id_entrega": "1",
                "percentual_contribuicao": 40,
            },
            {
                "id_contribuicao": "55501",
                "tipo_contribuicao": 2,
                "id_plano_entregas": None,
                "id_entrega": None,
                "percentual_contribuicao": 30,
            },
            {
                "id_contribuicao": "55504",
                "tipo_contribuicao": 1,
                "id_plano_entregas": "1",
                "id_entrega": "2",
                "percentual_contribuicao": 10,
            },
        ]

        response = self.put_plano_trabalho(input_pt)
        if response.status_code != status.HTTP_200_OK:
            print("response.json()", response.json())
        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)


class TestUpdatePTContribuicoesReferencias(BasePTTest):
    """Testes, quando da atualização de um Plano de Trabalho,
    relacionados à verificação de referências das Contribuições a outras
    tabelas.
    """

    def test_update_contribuicoes_outra_unidade_nao_permitida(
        self,
        example_pt,  # pylint: disable=unused-argument
        example_part_autorizadora_2,  # pylint: disable=unused-argument
        header_usr_2: dict,
    ):
        """Tenta atualizar um Plano de Trabalho com uma Contribuicao
        contendo id de uma outra unidade autorizadora e verifica se a
        Contribuicao original não foi, de fato, alterada.

        Args:
            example_pt: fixture que cria um Plano de Trabalho de exemplo
                na unidade autorizadora 1.
            example_part_autorizadora_2: fixture que cria um Participante
                de exemplo na unidade autorizadora 2.
            header_usr_2 (dict): Cabeçalho do usuário cadastrado em uma
                unidade autorizadora 2, diferente do exemplo.
        """
        # Passo 1 (fixtures example_pt e example_part_autorizadora_2):
        # - criar um Plano de Trabalho padrão na unidade 1
        # - criar um Participante na unidade 2
        # - consultar e guardar o id interno original da Contribucao que tem
        #   id_contribuicao == self.input_pt["contribuicoes"][0]["id"]
        response = self.get_plano_trabalho(
            cod_unidade_autorizadora=self.input_pt["cod_unidade_autorizadora"],
            id_plano_trabalho=self.input_pt["id_plano_trabalho"],
        )
        pt_original = response.json()
        lista_contribuicao_original = [
            item
            for item in pt_original["contribuicoes"]
            if item["id_contribuicao"]
            == self.input_pt["contribuicoes"][0]["id_contribuicao"]
        ]
        assert len(lista_contribuicao_original) == 1
        id_interno_original = lista_contribuicao_original[0].get("id", None)
        if id_interno_original is None:
            # O id interno não está sendo exposto, esse é o comportamento
            # correto. Desnecessário continuar testando.
            return
        tipo_contribuicao_original = lista_contribuicao_original[0]["tipo_contribuicao"]

        # Passo 2:
        # - criar, usando o usuário da unidade 2, um Plano de Trabalho
        #   na unidade 2, contendo uma Contribuicao com o mesmo id do
        #   plano de trabalho na unidade 1
        input_pt = deepcopy(self.input_pt)
        input_pt["cod_unidade_autorizadora"] = 2
        input_pt["matricula_siape"] = "1234567"
        input_pt["contribuicoes"] = [
            {
                "id": id_interno_original,
                "id_contribuicao": str(id_interno_original),
                "tipo_contribuicao": 2,  # diferente do original na unidade 1
                "id_plano_entregas": None,
                "id_entrega": None,
                "percentual_contribuicao": 40,
            }
        ]
        response = self.put_plano_trabalho(input_pt, header_usr=header_usr_2)

        # Verifica se a alteração foi, de fato, rejeitada, pois alteraria
        # uma contribuicao de outra unidade
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Alteração rejeitada por violar regras de integridade"
        assert detail_message in response.json().get("detail")

        # Passo 3:
        # - verificar se o Plano de Trabalho na unidade 1, criado
        #   originalmente, permanece com a sua contribuicao inalterada
        response = self.get_plano_trabalho(
            cod_unidade_autorizadora=self.input_pt["cod_unidade_autorizadora"],
            id_plano_trabalho=self.input_pt["id_plano_trabalho"],
        )
        assert response.status_code == status.HTTP_200_OK
        lista_contribuicao_original = [
            item
            for item in response.json()["contribuicoes"]
            if item["id_contribuicao"]
            == self.input_pt["contribuicoes"][0]["id_contribuicao"]
        ]
        assert len(lista_contribuicao_original) == 1
        tipo_contribuicao_atual = lista_contribuicao_original[0]["tipo_contribuicao"]
        assert tipo_contribuicao_atual == tipo_contribuicao_original
