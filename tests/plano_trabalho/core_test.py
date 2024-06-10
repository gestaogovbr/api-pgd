"""
Testes relacionados às funcionalidades básicas do plano de trabalho do
participante.
"""

from typing import Optional

from httpx import Client
from fastapi import status

import pytest

from util import assert_error_message

# grupos de campos opcionais e obrigatórios a testar

FIELDS_PLANO_TRABALHO = {
    "optional": tuple(),  # nenhum campo é opcional
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
        ["contribuicoes"],
        ["avaliacao_registros_execucao"],
    ),
}

FIELDS_CONTRIBUICAO = {
    "optional": (
        ["cod_unidade_autorizadora_externa"],
        ["id_plano_entrega"],
        ["id_entrega"],
    ),
    "mandatory": (
        ["origem_unidade"],
        ["id_contribuicao"],
        ["cod_unidade_instituidora"],
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
        ["cpf_participante"],
        ["data_inicio"],
        ["data_termino"],
        ["carga_horaria_disponivel"],
    ),
}


# Classe base de testes


class BasePTTest:
    """Classe base para testes de Plano de Trabalho."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        truncate_pt,  # pylint: disable=unused-argument
        example_pe,  # pylint: disable=unused-argument
        input_pt: dict,
        user1_credentials: dict,
        header_usr_1: dict,
        client: Client,
    ):
        """Configurar o ambiente de teste.

        Args:
            truncate_pe (callable): Fixture para truncar a tabela PE.
            truncate_pt (callable): Fixture para truncar a tabela PT.
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
                for avaliacao in plano_trabalho_1["avaliacao_registros_execucao"]
                for field, value in avaliacao.items()
                if field in FIELDS_AVALIACAO_REGISTROS_EXECUCAO["mandatory"]
            }
        )
        avaliacao_registros_execucao_2 = set(
            {
                field: value
                for avaliacao in plano_trabalho_2["avaliacao_registros_execucao"]
                for field, value in avaliacao.items()
                if field in FIELDS_AVALIACAO_REGISTROS_EXECUCAO["mandatory"]
            }
        )
        assert avaliacao_registros_execucao_1 == avaliacao_registros_execucao_2

    def create_pt(
        self,
        input_pt: dict,
        id_plano_trabalho: Optional[str] = None,
        cod_unidade_autorizadora: Optional[int] = None,
        header_usr: Optional[dict] = None,
    ):
        """Criar um Plano de Trabalho.

        Args:
            input_pt (dict): O dicionário de entrada do Plano de Trabalho.
            id_plano_trabalho (str): O ID do Plano de Trabalho.
            cod_unidade_autorizadora (int): O ID da unidade autorizadora.
            header_usr (dict): Cabeçalhos HTTP para o usuário.

        Returns:
            httpx.Response: A resposta da API.
        """
        if id_plano_trabalho is None:
            id_plano_trabalho = input_pt["id_plano_trabalho"]
        if cod_unidade_autorizadora is None:
            cod_unidade_autorizadora = input_pt["cod_unidade_autorizadora"]
        if header_usr is None:
            header_usr = self.header_usr_1

        # Criar o Plano de Trabalho
        response = self.client.put(
            (
                f"/organizacao/SIAPE/{cod_unidade_autorizadora}/"
                f"plano_trabalho/{id_plano_trabalho}"
            ),
            json=input_pt,
            headers=header_usr,
        )
        return response

    def get_pt(
        self,
        id_plano_trabalho: str,
        cod_unidade_autorizadora: int,
        header_usr: Optional[dict] = None,
    ):
        """Obter um Plano de Trabalho.

        Args:
            id_plano_trabalho (str): O ID do Plano de Trabalho.
            cod_unidade_autorizadora (int): O ID da unidade autorizadora.
            header_usr (dict): Cabeçalhos HTTP para o usuário.

        Returns:
            httpx.Response: A resposta da API.
        """
        if header_usr is None:
            header_usr = self.header_usr_1
        response = self.client.get(
            (
                f"/organizacao/SIAPE/{cod_unidade_autorizadora}/"
                f"plano_trabalho/{id_plano_trabalho}"
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
        response = self.create_pt(self.input_pt)

        assert response.status_code == status.HTTP_201_CREATED
        self.assert_equal_plano_trabalho(response.json(), self.input_pt)

        # Consulta API para conferir se a criação foi persistida
        response = self.get_pt(
            self.input_pt["id_plano_trabalho"],
            self.input_pt["cod_unidade_autorizadora"],
        )

        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), self.input_pt)

    @pytest.mark.parametrize(
        "data_inicio_pt",
        [
            ("2022-12-01",),
            ("2023-01-15",),
        ],
    )
    def test_data_inicio_check(
        self,
        input_pe: dict,
        data_inicio_pt: str,
    ):
        """Testa a criação de um Plano de Trabalho com diferentes datas de início.

        Args:
            input_pe (dict): Dados do PE usado como exemplo.
            data_inicio_pt (str): Data recebida como parâmetro de teste.
        """
        # Atualiza a data de início do Plano de Trabalho
        input_pt = self.input_pt.copy()
        input_pt["data_inicio"] = data_inicio_pt

        response = self.create_pt(input_pt, header_usr=self.header_usr_1)

        if data_inicio_pt < input_pe["data_inicio"]:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert_error_message(
                response,
                "A data de início do Plano de Trabalho não pode ser anterior "
                "à data de início do Plano de Entregas.",
            )
        else:
            assert response.status_code == status.HTTP_201_CREATED

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
        for field in field_list:
            del input_pt[field]

        input_pt["id_plano_trabalho"] = (
            f"{1800 + offset}"  # precisa ser um novo plano
        )

        # Act
        response = self.create_pt(input_pt)

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
        response = self.create_pt(
            input_pt, id_plano_trabalho="111", header_usr=self.header_usr_1
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Parâmetro id_plano_trabalho na URL e no JSON devem ser iguais"
        assert response.json().get("detail", None) == detail_message


class TestUpdatePlanoDeTrabalho(BasePTTest):
    """Testes para atualizar um Plano de Trabalho existente.

    A fixture example_pt, chamada no método setup da classe BasePPTTest
    cria um novo Plano de Trabalho na API. Ao chamar novamente a API com
    método create_pt da classe (que, por sua vez, usa o método PUT da
    API), o Plano de Trabalho receberá uma atualização com alguns campos
    de dados modificados.
    """

    @pytest.fixture(autouse=True)
    def create_example(
        self,
        example_pt,  # pylint: disable=unused-argument
        ):
        """Configurar o ambiente de teste.

        Args:
            example_pt (callable): Fixture que cria exemplo de PT.
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
        input_pt["cod_unidade_executora"] = 100  # Valor era 99
        input_pt["data_termino"] = "2023-01-31"  # Valor era "2023-01-15"
        response = self.create_pt(input_pt)

        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)

        # Consulta API para conferir se a alteração foi persistida
        response = self.get_pt(
            input_pt["id_plano_trabalho"],
            self.user1_credentials["cod_unidade_autorizadora"],
        )

        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)


class TestCreatePlanoTrabalhoContribuicoes(BasePTTest):
    """Testes relacionados às Contribuições ao criar um Plano de Trabalho."""

    @pytest.mark.parametrize(
        "tipo_contribuicao, cod_unidade_autorizadora_externa, id_plano_entrega, id_entrega",
        [
            (1, None, "1", "1"),
            (1, None, "2", "2"),
            (1, None, None, None),
            (2, None, "1", None),
            (2, None, None, None),
            (3, None, "1", "1"),
            (3, None, None, None),
        ],
    )
    def test_tipo_contribuicao(
        self,
        tipo_contribuicao: int,
        cod_unidade_autorizadora_externa: Optional[int],
        id_plano_entrega: Optional[str],
        id_entrega: Optional[str],
    ):
        """Testa a criação de um novo plano de trabalho, verificando as
        regras de validação para os campos relacionados à contribuição.

        O teste verifica as seguintes regras:

        1. Quando tipo_contribuicao == 1, os campos id_plano_entrega e
           id_entrega são obrigatórios.
        2. Quando tipo_contribuicao == 2, os campos
           cod_unidade_autorizadora_externa, id_plano_entrega e id_entrega
           não devem ser informados.
        3. Quando tipo_contribuicao == 3, os campos
           cod_unidade_autorizadora_externa, id_plano_entrega e id_entrega
           são obrigatórios.
        4. Quando tipo_contribuicao != 3, o campo
           cod_unidade_autorizadora_externa não deve ser informado.

        O teste envia uma requisição PUT para a rota
        "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
        com os dados de entrada atualizados de acordo com os parâmetros
        fornecidos. Verifica se a resposta possui o status HTTP correto (201
        Created ou 422 Unprocessable Entity) e se as mensagens de erro
        esperadas estão presentes na resposta.
        """
        self.input_pt["contribuicoes"][0]["tipo_contribuicao"] = tipo_contribuicao
        self.input_pt["contribuicoes"][0]["id_plano_entrega"] = id_plano_entrega
        self.input_pt["contribuicoes"][0]["id_entrega"] = id_entrega
        response = self.create_pt(self.input_pt, header_usr=self.header_usr_1)

        fields_entrega_externa = (
            cod_unidade_autorizadora_externa,
            id_plano_entrega,
            id_entrega,
        )
        error_messages = []
        if tipo_contribuicao == 1 and (id_plano_entrega is None or id_entrega is None):
            error_messages.append(
                "Os campos id_plano_entrega e id_entrega são obrigatórios "
                "quando tipo_contribuicao tiver o valor 1."
            )
        if tipo_contribuicao == 2 and any(fields_entrega_externa):
            error_messages.append(
                "Não se deve informar cod_unidade_autorizadora_externa, "
                "id_plano_entrega ou id_entrega quando tipo_contribuicao == 2"
            )
        if tipo_contribuicao == 3 and any(
            field is None for field in fields_entrega_externa
        ):
            error_messages.append(
                "Os campos cod_unidade_autorizadora_externa, id_plano_entrega e "
                "id_entrega são obrigatórios quando tipo_contribuicao == 3"
            )
        if tipo_contribuicao != 3 and cod_unidade_autorizadora_externa:
            error_messages.append(
                "Só se deve usar cod_unidade_autorizadora_externa "
                "quando tipo_contribuicao == 3"
            )
        if error_messages:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            for detail_message in error_messages:
                assert_error_message(response, detail_message)
        else:
            assert response.status_code == status.HTTP_201_CREATED


class TestGetPT(BasePTTest):
    """Testes para consultar um Plano de Trabalho."""
    def test_get_plano_trabalho(self):
        """Consulta um plano de trabalho existente."""
        # Inclui os campos de resposta do json que não estavam no template
        input_pt = self.input_pt.copy()
        input_pt["cancelado"] = False
        input_pt["contribuicoes"][1]["id_entrega"] = None
        input_pt["contribuicoes"][1]["descricao_contribuicao"] = None

        response = self.get_pt(
            input_pt["id_plano_trabalho"], input_pt["cod_unidade_autorizadora"]
        )

        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)

    def test_get_pt_inexistente(self):
        """Tenta acessar um plano de trabalho inexistente."""
        non_existent_id = "888888888"

        response = self.get_pt(
            non_existent_id, self.user1_credentials["cod_unidade_autorizadora"]
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json().get("detail", None) == "Plano de trabalho não encontrado"


@pytest.mark.parametrize("carga_horaria_disponivel", [-2, -1])
def test_create_pt_invalid_carga_horaria_disponivel(
    input_pt: dict,
    carga_horaria_disponivel: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Testa a criação de um plano de trabalho com um valor inválido para
    o campo carga_horaria_disponivel.

    O teste envia uma requisição PUT para a rota
    "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
    com um valor negativo para o campo carga_horaria_disponivel.
    Espera-se que a resposta tenha o status HTTP 422 Unprocessable Entity
    e que a mensagem de erro "Valor de carga_horaria_disponivel deve ser
    maior ou igual a zero" esteja presente na resposta.
    """
    input_pt["carga_horaria_disponivel"] = carga_horaria_disponivel
    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_message = "Valor de carga_horaria_disponivel deve ser maior ou igual a zero"
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
def test_put_plano_trabalho_invalid_cpf(
    input_pt: dict,
    cpf_participante: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    client: Client,
):
    """Testa o envio de um plano de trabalho com um CPF inválido.

    O teste envia uma requisição PUT para a rota
    "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
    com um valor inválido para o campo cpf_participante. Espera-se que a
    resposta tenha o status HTTP 422 Unprocessable Entity e que uma das
    seguintes mensagens de erro esteja presente na resposta: - "Dígitos
    verificadores do CPF inválidos." - "CPF inválido." - "CPF precisa ter
    11 dígitos." - "CPF deve conter apenas dígitos."
    """
    input_pt["cpf_participante"] = cpf_participante

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )
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
