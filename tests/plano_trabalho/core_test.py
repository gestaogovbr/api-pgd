"""
Testes relacionados às funcionalidades básicas do plano de trabalho do
participante.
"""

from typing import Optional

from httpx import Client, Response
from fastapi import status

import pytest

from util import assert_error_message

# grupos de campos opcionais e obrigatórios a testar

FIELDS_PLANO_TRABALHO = {
    "optional": (
        ["avaliacoes_registros_execucao"],
        ["contribuicoes"],
    ),
    "mandatory": (
        ["origem_unidade"],
        ["cod_unidade_autorizadora"],
        ["id_plano_trabalho"],
        ["status"],
        ["cod_unidade_executora"],
        ["cpf_participante"],
        ["matricula_siape"],
        ["data_inicio"],
        ["data_termino"],
        ["carga_horaria_disponivel"],
    ),
}

FIELDS_CONTRIBUICAO = {
    "optional": (
        ["id_plano_entregas"],
        ["id_entrega"],
        ["contribuicoes"],
        ["avaliacoes_registros_execucao"],
    ),
    "mandatory": (
        ["id_contribuicao"],
        ["tipo_contribuicao"],
        ["percentual_contribuicao"],
        ["carga_horaria_disponivel"],
    ),
}

FIELDS_AVALIACAO_REGISTROS_EXECUCAO = {
    "optional": tuple(),  # nenhum campo é opcional
    "mandatory": (
        ["id_periodo_avaliativo"],
        ["data_inicio_periodo_avaliativo"],
        ["data_fim_periodo_avaliativo"],
        ["avaliacao_registros_execucao"],
        ["data_avaliacao_registros_execucao"],
    ),
}


# Classe base de testes


class BasePTTest:
    """Classe base para testes de Plano de Trabalho."""

    # pylint: disable=too-many-arguments
    @pytest.fixture(autouse=True)
    def setup(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        truncate_pt,  # pylint: disable=unused-argument
        example_pe,  # pylint: disable=unused-argument
        example_part,  # pylint: disable=unused-argument
        input_pt: dict,
        user1_credentials: dict,
        header_usr_1: dict,
        client: Client,
    ):
        """Configurar o ambiente de teste.

        Args:
            truncate_pe (callable): Fixture para truncar a tabela de
                Planos de Entrega.
            truncate_pt (callable): Fixture para truncar a tabela de
                Planos de Trabalho.
            example_pe (callable): Fixture que cria exemplo de PE.
            input_pt (dict): Dados usados para ciar um PT
            user1_credentials (dict): Credenciais do usuário 1.
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
            client (Client): Uma instância do cliente HTTPX.
        """
        # pylint: disable=attribute-defined-outside-init
        self.input_pt = input_pt
        self.user1_credentials = user1_credentials
        self.header_usr_1 = header_usr_1
        self.client = client

    @staticmethod
    def assert_equal_plano_trabalho(plano_trabalho_1: dict, plano_trabalho_2: dict):
        """Verifica a igualdade de dois planos de trabalho, considerando
        apenas os campos obrigatórios.
        """
        # Compara o conteúdo de todos os campos obrigatórios do plano de
        # trabalho, exceto as listas de contribuições e avaliacao_registros_execucao
        assert all(
            plano_trabalho_1[attribute] == plano_trabalho_2[attribute]
            for attributes in FIELDS_PLANO_TRABALHO["mandatory"]
            for attribute in attributes
            if attribute not in ("contribuicoes", "avaliacao_registros_execucao")
        )

        # Compara o conteúdo de cada contribuição, somente campos obrigatórios
        contribuicoes_1 = set(
            {
                field: value
                for contribuicao in plano_trabalho_1["contribuicoes"]
                for field, value in contribuicao.items()
                if field in FIELDS_CONTRIBUICAO["mandatory"]
            }
        )
        contribuicoes_2 = set(
            {
                field: value
                for contribuicao in plano_trabalho_2["contribuicoes"]
                for field, value in contribuicao.items()
                if field in FIELDS_CONTRIBUICAO["mandatory"]
            }
        )
        assert contribuicoes_1 == contribuicoes_2

        # Compara o conteúdo de cada avaliacao_registros_execucao, somente campos obrigatórios
        avaliacao_registros_execucao_1 = set(
            {
                field: value
                for avaliacao in plano_trabalho_1["avaliacoes_registros_execucao"]
                for field, value in avaliacao.items()
                if field in FIELDS_AVALIACAO_REGISTROS_EXECUCAO["mandatory"]
            }
        )
        avaliacao_registros_execucao_2 = set(
            {
                field: value
                for avaliacao in plano_trabalho_2["avaliacoes_registros_execucao"]
                for field, value in avaliacao.items()
                if field in FIELDS_AVALIACAO_REGISTROS_EXECUCAO["mandatory"]
            }
        )
        assert avaliacao_registros_execucao_1 == avaliacao_registros_execucao_2

    def put_plano_trabalho(
        self,
        input_pt: dict,
        id_plano_trabalho: Optional[str] = None,
        origem_unidade: Optional[str] = None,
        cod_unidade_autorizadora: Optional[int] = None,
        header_usr: Optional[dict] = None,
    ) -> Response:
        """Cria ou atualiza um Plano de Trabalho pela API, usando o verbo PUT.

        Args:
            input_pt (dict): O dicionário de entrada do Plano de Trabalho.
            id_plano_trabalho (str): O ID do Plano de Trabalho.
            origem_unidade (str): origem do código da unidade.
            cod_unidade_autorizadora (int): O ID da unidade autorizadora.
            header_usr (dict): Cabeçalhos HTTP para o usuário.

        Returns:
            httpx.Response: A resposta da API.
        """
        if id_plano_trabalho is None:
            id_plano_trabalho = input_pt["id_plano_trabalho"]
        if origem_unidade is None:
            origem_unidade = input_pt["origem_unidade"]
        if cod_unidade_autorizadora is None:
            cod_unidade_autorizadora = input_pt["cod_unidade_autorizadora"]
        if header_usr is None:
            header_usr = self.header_usr_1

        # Criar o Plano de Trabalho
        response = self.client.put(
            (
                f"/organizacao/{origem_unidade}/{cod_unidade_autorizadora}/"
                f"plano_trabalho/{id_plano_trabalho}"
            ),
            json=input_pt,
            headers=header_usr,
        )
        return response

    def get_plano_trabalho(
        self,
        id_plano_trabalho: str,
        cod_unidade_autorizadora: int,
        origem_unidade: Optional[str] = "SIAPE",
        header_usr: Optional[dict] = None,
    ) -> Response:
        """Obtém um Plano de Trabalho pela API, usando o verbo GET.

        Args:
            id_plano_trabalho (str): O ID do Plano de Trabalho.
            cod_unidade_autorizadora (int): O ID da unidade autorizadora.
            origem_unidade (str): origem do código da unidade.
            header_usr (dict): Cabeçalhos HTTP para o usuário.

        Returns:
            httpx.Response: A resposta da API.
        """
        if header_usr is None:
            header_usr = self.header_usr_1
        response = self.client.get(
            (
                f"/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
                f"/plano_trabalho/{id_plano_trabalho}"
            ),
            headers=header_usr,
        )
        return response


class TestCreatePlanoTrabalho(BasePTTest):
    """Testes para criação de Plano de Trabalho."""

    def test_completo(self):
        """Cria um novo Plano de Trabalho do Participante, em uma unidade
        na qual ele está autorizado, contendo todos os dados necessários.
        """
        response = self.put_plano_trabalho(self.input_pt)

        assert response.status_code == status.HTTP_201_CREATED
        self.assert_equal_plano_trabalho(response.json(), self.input_pt)

        # Consulta API para conferir se a criação foi persistida
        response = self.get_plano_trabalho(
            self.input_pt["id_plano_trabalho"],
            self.input_pt["cod_unidade_autorizadora"],
        )

        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), self.input_pt)

    @pytest.mark.parametrize(
        "missing_fields", enumerate(FIELDS_PLANO_TRABALHO["mandatory"])
    )
    def test_create_plano_trabalho_missing_mandatory_fields(self, missing_fields):
        """Tenta criar um plano de trabalho, faltando campos obrigatórios.
        Tem que ser um plano de trabalho novo, pois na atualização de um
        plano de trabalho existente, o campo que ficar faltando será
        interpretado como um campo que não será atualizado, ainda que seja
        obrigatório para a criação.
        """
        # Arrange
        offset, field_list = missing_fields
        input_pt = self.input_pt.copy()
        # Estes campos fazem parte da URL e para omiti-los será necessário
        # inclui-los na chamada do método create_pt
        fields_in_url = [
            "origem_unidade",
            "cod_unidade_autorizadora",
            "id_plano_trabalho",
        ]
        placeholder_fields = {}
        for field in field_list:
            if field in fields_in_url:
                placeholder_fields[field] = input_pt[field]
            del input_pt[field]

        input_pt["id_plano_trabalho"] = f"{1800 + offset}"  # precisa ser um novo plano

        # Act
        response = self.put_plano_trabalho(input_pt, **placeholder_fields)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_pt_cod_plano_inconsistent(self):
        """Tenta criar um plano de trabalho com um códigos diferentes
        informados na URL e no campo id_plano_trabalho do JSON.
        """
        # Arrange
        input_pt = self.input_pt.copy()
        input_pt["id_plano_trabalho"] = "110"

        # Act
        response = self.put_plano_trabalho(
            input_pt, id_plano_trabalho="111", header_usr=self.header_usr_1
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Parâmetro id_plano_trabalho na URL e no JSON devem ser iguais"
        assert response.json().get("detail", None) == detail_message

    @pytest.mark.parametrize("carga_horaria_disponivel", [-2, -1])
    def test_create_pt_invalid_carga_horaria_disponivel(self, carga_horaria_disponivel):
        """Testa a criação de um plano de trabalho com um valor inválido para
        o campo carga_horaria_disponivel.

        O teste envia uma requisição PUT para a rota
        "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
        com um valor negativo para o campo carga_horaria_disponivel.
        Espera-se que a resposta tenha o status HTTP 422 Unprocessable Entity
        e que a mensagem de erro "Valor de carga_horaria_disponivel deve ser
        maior ou igual a zero" esteja presente na resposta.
        """
        # Arrange
        input_pt = self.input_pt.copy()
        input_pt["carga_horaria_disponivel"] = carga_horaria_disponivel

        # Act
        response = self.put_plano_trabalho(input_pt)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = (
            "Valor de carga_horaria_disponivel deve ser maior ou igual a zero"
        )
        assert_error_message(response, detail_message)

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
    def test_put_plano_trabalho_invalid_cpf(self, cpf_participante):
        """Testa o envio de um plano de trabalho com um CPF inválido.

        O teste envia uma requisição PUT para a rota
        "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
        com um valor inválido para o campo cpf_participante. Espera-se que a
        resposta tenha o status HTTP 422 Unprocessable Entity e que uma das
        seguintes mensagens de erro esteja presente na resposta:
        - "Dígitos verificadores do CPF inválidos."
        - "CPF inválido."
        - "CPF precisa ter 11 dígitos."
        - "CPF deve conter apenas dígitos."
        """
        # Arrange
        input_pt = self.input_pt.copy()
        input_pt["cpf_participante"] = cpf_participante

        # Act
        response = self.put_plano_trabalho(input_pt)

        # Assert
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


class TestUpdatePlanoDeTrabalho(BasePTTest):
    """Testes para atualizar um Plano de Trabalho existente.

    A fixture example_pt, chamada no método setup da classe BasePPTTest
    cria um novo Plano de Trabalho na API. Ao chamar novamente a API com
    método create_pt da classe (que, por sua vez, usa o método PUT da
    API), o Plano de Trabalho receberá uma atualização com alguns campos
    de dados modificados.
    """

    def test_update_plano_trabalho(self):
        """Atualiza um Plano de Trabalho existente usando o método HTTP
        PUT. Como o Plano de Trabalho já existe, o código HTTP retornado
        deve ser 200 OK, em vez de 201 Created.

        Além disso, obtém os dados novamente por método HTTP GET e
        verifica se a alteração foi persistida.
        """
        # Altera campos do PT e reenvia pra API (update)

        input_pt = self.input_pt.copy()
        input_pt["status"] = 4  # Valor era 3
        input_pt["data_termino"] = "2023-01-31"  # Valor era "2023-01-15"
        response = self.put_plano_trabalho(input_pt)
        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)

        # Consulta API para conferir se a alteração foi persistida
        response = self.get_plano_trabalho(
            input_pt["id_plano_trabalho"],
            self.user1_credentials["cod_unidade_autorizadora"],
        )

        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)


class TestGetPlanoTrabalho(BasePTTest):
    """Testes para consultar um Plano de Trabalho."""

    def test_get_plano_trabalho(self, example_pt):  # pylint: disable=unused-argument
        """Consulta um plano de trabalho existente."""
        # Inclui os campos de resposta do json que não estavam no template
        input_pt = self.input_pt.copy()
        input_pt["cancelado"] = False
        input_pt["contribuicoes"][1]["id_entrega"] = None
        input_pt["contribuicoes"][1]["descricao_contribuicao"] = None

        response = self.get_plano_trabalho(
            input_pt["id_plano_trabalho"], input_pt["cod_unidade_autorizadora"]
        )

        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)

    def test_get_pt_inexistente(self):
        """Tenta acessar um plano de trabalho inexistente."""
        non_existent_id = "888888888"

        response = self.get_plano_trabalho(
            non_existent_id, self.user1_credentials["cod_unidade_autorizadora"]
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json().get("detail", None) == "Plano de trabalho não encontrado"
