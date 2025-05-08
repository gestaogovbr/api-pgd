"""
Testes relacionados ao Plano de Entregas da Unidade
"""

from copy import deepcopy
from typing import Optional

from httpx import Client, Response
from fastapi import status as http_status

import pytest

from util import assert_error_message
from ..conftest import MAX_BIGINT

# constantes

STR_MAX_SIZE = 300

# grupos de campos opcionais e obrigatórios a testar

FIELDS_PLANO_ENTREGAS = {
    "optional": (
        ["avaliacao"],
        ["data_avaliacao"],
    ),
    "mandatory": (
        ["origem_unidade"],
        ["cod_unidade_autorizadora"],
        ["cod_unidade_instituidora"],
        ["cod_unidade_executora"],
        ["id_plano_entregas"],
        ["status"],
        ["data_inicio"],
        ["data_termino"],
        ["entregas"],
    ),
}

FIELDS_ENTREGA = {
    "optional": (["entrega_cancelada"],),
    "mandatory": (
        ["id_entrega"],
        ["nome_entrega"],
        ["meta_entrega"],
        ["tipo_meta"],
        ["data_entrega"],
        ["nome_unidade_demandante"],
        ["nome_unidade_destinataria"],
    ),
}


# Classe base de testes


class BasePETest:
    """Classe base para testes de Plano de Entregas."""

    # pylint: disable=too-many-arguments
    @pytest.fixture(autouse=True)
    def setup(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        input_pe: dict,
        user1_credentials: dict,
        header_usr_1: dict,
        client: Client,
    ):
        """Configurar o ambiente de teste.

        Args:
            truncate_pe (callable): Fixture para truncar a tabela de
                Planos de Entrega (PE).
            input_pe (dict): Dados usados para criar um PE.
            user1_credentials (dict): Credenciais do usuário 1.
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
            client (Client): Uma instância do cliente HTTPX.
        """
        # pylint: disable=attribute-defined-outside-init
        self.input_pe = input_pe
        self.user1_credentials = user1_credentials
        self.header_usr_1 = header_usr_1
        self.client = client

    @staticmethod
    def assert_equal_plano_entregas(plano_entregas_1: dict, plano_entregas_2: dict):
        """Verifica a igualdade de dois planos de entregas, considerando
        apenas os campos obrigatórios.
        """
        # Compara o conteúdo de todos os campos obrigatórios do plano de
        # entregas, exceto a lista de entregas
        assert all(
            plano_entregas_1[attribute] == plano_entregas_2[attribute]
            for attributes in FIELDS_PLANO_ENTREGAS["mandatory"]
            for attribute in attributes
            if attribute not in ("entregas")
        )

        # Compara o conteúdo de cada entrega, somente campos obrigatórios
        first_plan_by_entrega = {
            entrega["id_entrega"]: entrega for entrega in plano_entregas_1["entregas"]
        }
        second_plan_by_entrega = {
            entrega["id_entrega"]: entrega for entrega in plano_entregas_2["entregas"]
        }
        assert all(
            first_plan_by_entrega[id_entrega][attribute] == entrega[attribute]
            for attributes in FIELDS_ENTREGA["mandatory"]
            for attribute in attributes
            for id_entrega, entrega in second_plan_by_entrega.items()
        )

    def put_plano_entregas(
        self,
        input_pe: dict,
        id_plano_entregas: Optional[str] = None,
        origem_unidade: Optional[str] = None,
        cod_unidade_autorizadora: Optional[int] = None,
        header_usr: Optional[dict] = None,
    ) -> Response:
        """Cria ou atualiza um Plano de Entregas pela API, usando o método
        PUT.

        Args:
            input_pe (dict): O dicionário de entrada do Plano de Entregas.
            id_plano_entregas (str): O ID do Plano de Entregas.
            origem_unidade (str): origem do código da unidade.
            cod_unidade_autorizadora (int): O ID da unidade autorizadora.
            header_usr (dict): Cabeçalhos HTTP para o usuário.

        Returns:
            httpx.Response: A resposta da API.
        """
        if id_plano_entregas is None:
            id_plano_entregas = input_pe["id_plano_entregas"]
        if origem_unidade is None:
            origem_unidade = input_pe["origem_unidade"]
        if cod_unidade_autorizadora is None:
            cod_unidade_autorizadora = self.user1_credentials[
                "cod_unidade_autorizadora"
            ]
        if header_usr is None:
            header_usr = self.header_usr_1

        response = self.client.put(
            (
                f"/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
                f"/plano_entregas/{id_plano_entregas}"
            ),
            json=input_pe,
            headers=header_usr,
        )
        return response

    def get_plano_entregas(
        self,
        id_plano_entregas: str,
        cod_unidade_autorizadora: int,
        origem_unidade: Optional[str] = "SIAPE",
        header_usr: Optional[dict] = None,
    ) -> Response:
        """Obtém um Plano de Entregas pela API, usando o verbo GET.

        Args:
            id_plano_entregas (str): O ID do Plano de Entregas.
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
                f"/plano_entregas/{id_plano_entregas}"
            ),
            headers=header_usr,
        )
        return response


# Os testes usam muitas fixtures, então necessariamente precisam de
# muitos argumentos. Além disso, algumas fixtures não retornam um valor
# para ser usado no teste, mas mesmo assim são executadas quando estão
# presentes como um argumento da função.
# A linha abaixo desabilita os warnings do Pylint sobre isso.
# pylint: disable=too-many-arguments


class TestCreatePlanoEntrega(BasePETest):
    """Testes para a criação de um novo Plano de Entregas."""

    def test_create_plano_entregas_completo(self):
        """Testa a criação de um Plano de Entregas completo.

        Verifica se a API retorna um status 201 Created quando um novo Plano de Entregas
        é criado com sucesso, se a resposta não contém uma mensagem de erro e se o
        Plano de Entregas criado é igual ao Plano de Entregas enviado na requisição.
        """

        response = self.put_plano_entregas(self.input_pe)
        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.json().get("detail", None) is None
        self.assert_equal_plano_entregas(response.json(), self.input_pe)

    def test_update_plano_entregas(self, example_pe):  # pylint: disable=unused-argument
        """Tenta criar um novo Plano de Entregas e atualizar alguns campos.
        A fixture example_pe cria um Plano de Entregas de exemplo usando a API.
        O teste altera um campo do PE e reenvia pra API (update).
        """

        input_pe = deepcopy(self.input_pe)
        input_pe["avaliacao"] = 3
        input_pe["data_avaliacao"] = "2023-08-15"
        response = self.put_plano_entregas(input_pe)
        assert response.status_code == http_status.HTTP_200_OK
        assert response.json()["avaliacao"] == 3
        assert response.json()["data_avaliacao"] == "2023-08-15"

        # Consulta API para conferir se a alteração foi persistida
        response = self.get_plano_entregas(
            input_pe["id_plano_entregas"],
            self.user1_credentials["cod_unidade_autorizadora"],
        )
        assert response.status_code == http_status.HTTP_200_OK
        assert response.json()["avaliacao"] == 3
        assert response.json()["data_avaliacao"] == "2023-08-15"

    @pytest.mark.parametrize("omitted_fields", enumerate(FIELDS_ENTREGA["optional"]))
    def test_create_plano_entregas_entrega_omit_optional_fields(self, omitted_fields):
        """Tenta criar um novo Plano de Entregas omitindo campos opcionais.

        Verifica se a API retorna um status 201 Created, o que indica ter sido
        criado com sucesso.
        """

        input_pe = deepcopy(self.input_pe)
        offset, field_list = omitted_fields
        for field in field_list:
            for entrega in input_pe["entregas"]:
                if field in entrega:
                    del entrega[field]

        input_pe["id_plano_entregas"] = str(557 + offset)
        response = self.put_plano_entregas(input_pe)
        assert response.status_code == http_status.HTTP_201_CREATED
        self.assert_equal_plano_entregas(response.json(), input_pe)

    @pytest.mark.parametrize("nulled_fields", enumerate(FIELDS_ENTREGA["optional"]))
    def test_create_plano_entregas_entrega_null_optional_fields(self, nulled_fields):
        """Tenta criar um novo Plano de Entregas, preenchendo com o valor null
        os campos opcionais.

        Verifica se a API retorna um status 201 Created, o que indica ter sido
        criado com sucesso."""

        input_pe = deepcopy(self.input_pe)
        offset, field_list = nulled_fields
        for field in field_list:
            for entrega in input_pe["entregas"]:
                if field in entrega:
                    entrega[field] = None

        input_pe["id_plano_entregas"] = str(557 + offset)
        response = self.put_plano_entregas(input_pe)
        assert response.status_code == http_status.HTTP_201_CREATED
        self.assert_equal_plano_entregas(response.json(), input_pe)

    @pytest.mark.parametrize(
        "missing_fields", enumerate(FIELDS_PLANO_ENTREGAS["mandatory"])
    )
    def test_create_plano_entregas_missing_mandatory_fields(self, missing_fields):
        """Tenta criar um Plano de Entregas, faltando campos obrigatórios.
        Na atualização com PUT, ainda assim é necessário informar todos os
        campos obrigatórios, uma vez que o conteúdo será substituído.

        Verifica se a API retorna um status 422 Unprocessable Entity, o que
        indica que a entrada foi rejeitada, conforme o esperado.
        """

        offset, field_list = missing_fields
        input_pe = deepcopy(self.input_pe)
        # define um id_plano_entregas diferente para cada teste
        input_pe["id_plano_entregas"] = 1800 + offset
        # Estes campos fazem parte da URL e para omiti-los será necessário
        # inclui-los na chamada do método create_pe
        fields_in_url = [
            "origem_unidade",
            "cod_unidade_autorizadora",
            "id_plano_entregas",
        ]
        placeholder_fields = {}
        for field in field_list:
            if field in fields_in_url:
                placeholder_fields[field] = input_pe[field]
            del input_pe[field]

        # Act
        response = self.put_plano_entregas(input_pe, **placeholder_fields)

        # Assert
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_huge_plano_entregas(self):
        """Testa a criação de um Plano de Entregas com grande volume de dados.
        Os campos que aceitam entrada livre de texto são preenchidos com textos
        longos.
        """

        input_pe = deepcopy(self.input_pe)

        def create_huge_entrega(id_entrega: int) -> dict:
            """Cria uma Entrega que ocupa bastante espaço de dados.

            Args:
                id_entrega (int): o id da Entrega.

            Returns:
                dict: os dados da Entrega.
            """
            new_entrega = input_pe["entregas"][0].copy()
            new_entrega["id_entrega"] = str(3 + id_entrega)
            new_entrega["nome_entrega"] = "x" * 300  # 300 caracteres
            new_entrega["nome_unidade_demandante"] = "x" * 300  # 300 caracteres
            new_entrega["nome_unidade_destinataria"] = "x" * 300  # 300 caracteres
            return new_entrega

        for id_entrega in range(200):
            input_pe["entregas"].append(create_huge_entrega(id_entrega))

        response = self.put_plano_entregas(input_pe)
        assert response.status_code == http_status.HTTP_201_CREATED
        self.assert_equal_plano_entregas(response.json(), input_pe)

        response_by_entrega = {
            entrega["id_entrega"]: entrega for entrega in response.json()["entregas"]
        }
        input_by_entrega = {
            entrega["id_entrega"]: entrega for entrega in input_pe["entregas"]
        }
        assert all(
            response_by_entrega[id_entrega][attribute] == entrega[attribute]
            for attributes in FIELDS_ENTREGA["mandatory"]
            for attribute in attributes
            for id_entrega, entrega in input_by_entrega.items()
        )

class TestCreatePEInputValidation(BasePETest):
    """Testes para a validação de entrada na criação de um Plano de Entregas."""

    @pytest.mark.parametrize(
        "id_plano_entregas, nome_entrega, nome_unidade_demandante, nome_unidade_destinataria",
        [
            ("1", "x" * 301, "string", "string"),
            ("2", "string", "x" * 301, "string"),
            ("3", "string", "string", "x" * 301),
            ("4", "x" * 300, "x" * 300, "x" * 300),
        ],
    )
    def test_create_pe_exceed_string_max_size(
        self,
        id_plano_entregas: str,
        nome_entrega: str,  # 300 caracteres
        nome_unidade_demandante: str,  # 300 caracteres
        nome_unidade_destinataria: str,  # 300 caracteres
    ):
        """Testa a criação de um plano de entregas excedendo o tamanho
        máximo de cada campo.
        """

        input_pe = deepcopy(self.input_pe)
        input_pe["id_plano_entregas"] = id_plano_entregas
        input_pe["entregas"][0]["nome_entrega"] = nome_entrega  # 300 caracteres
        input_pe["entregas"][0][
            "nome_unidade_demandante"
        ] = nome_unidade_demandante  # 300 caracteres
        input_pe["entregas"][0][
            "nome_unidade_destinataria"
        ] = nome_unidade_destinataria  # 300 caracteres

        response = self.put_plano_entregas(input_pe)

        if any(
            len(campo) > STR_MAX_SIZE
            for campo in (
                nome_entrega,
                nome_unidade_demandante,
                nome_unidade_destinataria,
            )
        ):
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "String should have at most 300 characters"
            assert response.json().get("detail")[0]["msg"] == detail_message
        else:
            assert response.status_code == http_status.HTTP_201_CREATED

    def test_create_pe_cod_plano_inconsistent(
        self,
        truncate_pe,  # pylint: disable=unused-argument
    ):
        """Tenta criar um plano de entregas com código de plano divergente"""

        input_pe = deepcopy(self.input_pe)
        input_pe["id_plano_entregas"] = "110"
        response = self.put_plano_entregas(
            input_pe, id_plano_entregas="111"  # diferente de 110
        )
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = "Parâmetro id_plano_entregas na URL e no JSON devem ser iguais"
        assert response.json().get("detail", None) == detail_msg

    def test_create_pe_cod_unidade_inconsistent(
        self,
        truncate_pe,  # pylint: disable=unused-argument
    ):
        """Tenta criar um plano de entregas com código de unidade divergente"""

        input_pe = deepcopy(self.input_pe)
        original_input_pe = input_pe.copy()
        input_pe["cod_unidade_autorizadora"] = 999  # era 1
        response = self.put_plano_entregas(
            input_pe,
            cod_unidade_autorizadora=original_input_pe["cod_unidade_autorizadora"],
            id_plano_entregas=original_input_pe["id_plano_entregas"],
        )
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = (
            "Parâmetro cod_unidade_autorizadora na URL e no JSON devem ser iguais"
        )
        assert response.json().get("detail", None) == detail_msg

    @pytest.mark.parametrize("cod_unidade_executora", [99, 0, -1])
    def test_create_invalid_cod_unidade(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        cod_unidade_executora: int,
    ):
        """Tenta criar uma entrega com código de unidade inválido.
        Por ora não será feita validação no sistema, e sim apenas uma
        verificação de sanidade.
        """

        input_pe = deepcopy(self.input_pe)
        input_pe["cod_unidade_executora"] = cod_unidade_executora

        response = self.put_plano_entregas(input_pe)

        if cod_unidade_executora > 0:
            assert response.status_code == http_status.HTTP_201_CREATED
        else:
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "Input should be greater than 0"
            assert any(
                detail_message in error["msg"]
                for error in response.json().get("detail")
            )

    @pytest.mark.parametrize(
        "id_plano_entregas, meta_entrega, tipo_meta",
        [
            ("555", 10, "unidade"),
            ("556", -10, "percentual"),
            ("557", 1, "percentual"),
            ("558", -10, "unidade"),
            ("559", 200, "percentual"),
            ("560", 0, "unidade"),
        ],
    )
    def test_create_entrega_invalid_percent(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        id_plano_entregas: str,
        meta_entrega: int,
        tipo_meta: str,
    ):
        """Tenta criar um Plano de Entregas com meta_entrega com valores inválidos"""

        input_pe = deepcopy(self.input_pe)
        input_pe["id_plano_entregas"] = id_plano_entregas
        input_pe["entregas"][1]["meta_entrega"] = meta_entrega
        input_pe["entregas"][1]["tipo_meta"] = tipo_meta

        response = self.put_plano_entregas(input_pe)

        if meta_entrega < 0:
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "Input should be greater than or equal to 0"
            assert any(
                detail_message in error["msg"]
                for error in response.json().get("detail")
            )
        else:
            assert response.status_code == http_status.HTTP_201_CREATED

    @pytest.mark.parametrize("tipo_meta", ["unidade", "percentual", "invalid"])
    def test_create_entrega_invalid_tipo_meta(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        tipo_meta: str,
    ):
        """Tenta criar um Plano de Entregas com tipo de meta inválido"""

        input_pe = deepcopy(self.input_pe)
        input_pe["entregas"][0]["tipo_meta"] = tipo_meta

        response = self.put_plano_entregas(input_pe)

        if tipo_meta in ("unidade", "percentual"):
            assert response.status_code == http_status.HTTP_201_CREATED
        else:
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = "Input should be 'unidade' or 'percentual'"
            assert any(
                detail_message in error["msg"]
                for error in response.json().get("detail")
            )

    @pytest.mark.parametrize("avaliacao", [-1, 0, 1, 6])
    def test_create_pe_invalid_avaliacao(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        avaliacao: int,
    ):
        """Tenta criar um Plano de Entregas com nota de avaliação inválida"""

        input_pe = deepcopy(self.input_pe)
        input_pe["avaliacao"] = avaliacao
        response = self.put_plano_entregas(input_pe)

        if avaliacao in range(1, 6):
            assert response.status_code == http_status.HTTP_201_CREATED
        else:
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_messages = [
                "Input should be greater than 0",
                "Input should be less than or equal to 5",
            ]
            assert any(
                detail_message == error["msg"]
                for error in response.json().get("detail", {})
                for detail_message in detail_messages
            )

    @pytest.mark.parametrize(
        "id_plano_entregas, status, avaliacao, data_avaliacao",
        [
            ("78", 5, 2, "2023-06-11"),
            ("79", 5, 2, None),  # falta data_avaliacao
            ("80", 5, None, "2023-06-11"),  # falta avaliacao
            ("81", 5, None, None),  # faltam ambos
            ("81", 2, None, None),  # status não é 5
        ],
    )
    def test_create_pe_status_avaliado(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        id_plano_entregas: str,
        status: int,
        avaliacao: int,
        data_avaliacao: str,
    ):
        """Tenta criar um plano de entregas com datas de avaliação omitidas
        ou preenchidas, a depender do status.

        O status 5 só poderá ser usado se os campos "avaliacao" e "data_avaliacao"
        estiverem preenchidos.
        """

        input_pe = deepcopy(self.input_pe)
        input_pe["status"] = status
        input_pe["avaliacao"] = avaliacao
        input_pe["data_avaliacao"] = data_avaliacao
        input_pe["id_plano_entregas"] = id_plano_entregas

        response = self.put_plano_entregas(input_pe)

        if status == 5 and not (avaliacao and data_avaliacao):
            assert response.status_code == 422
            detail_message = (
                "O status 5 só poderá ser usado se os campos avaliacao e "
                "data_avaliacao estiverem preenchidos."
            )
            assert_error_message(response, detail_message)
        else:
            assert response.status_code == http_status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        (
            "cod_unidade_autorizadora, cod_unidade_instituidora, "
            "cod_unidade_executora"
        ),
        [
            (-1, 99, 99),  # cod_unidade_autorizadora negativo
            (1, -1, 99),  # cod_unidade_instituidora negativo
            (1, 99, -1),  # cod_unidade_executora negativo
            (MAX_BIGINT, 99, 99),  # cod_unidade_autorizadora igual a MAX_BIGINT
            (1, MAX_BIGINT, 99),  # cod_unidade_instituidora igual a MAX_BIGINT
            (1, 99, MAX_BIGINT),  # cod_unidade_executora igual a MAX_BIGINT
            (MAX_BIGINT + 1, 99, 99),  # cod_unidade_autorizadora maior que MAX_BIGINT
            (1, MAX_BIGINT + 1, 99),  # cod_unidade_instituidora maior que MAX_BIGINT
            (1, 99, MAX_BIGINT + 1),  # cod_unidade_executora maior que MAX_BIGINT
        ],
    )
    def test_create_plano_entregas_int_out_of_range(
        self,
        cod_unidade_autorizadora: int,
        cod_unidade_instituidora: int,
        cod_unidade_executora: int,
    ):
        """Testa a criação e um participante usando valores de unidade
        fora dos limites estabelecidos.
        """
        input_pe = deepcopy(self.input_pe)
        input_pe["cod_unidade_autorizadora"] = cod_unidade_autorizadora
        input_pe["cod_unidade_instituidora"] = cod_unidade_instituidora
        input_pe["cod_unidade_executora"] = cod_unidade_executora

        response = self.put_plano_entregas(
            input_pe, cod_unidade_autorizadora=cod_unidade_autorizadora
        )

        if all(
            (
                (0 < input_pe.get(field) <= MAX_BIGINT)
                for field in (
                    "cod_unidade_autorizadora",
                    "cod_unidade_instituidora",
                    "cod_unidade_executora",
                )
            )
        ):
            assert response.status_code == http_status.HTTP_201_CREATED
        else:
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        ("entregas", "status"),
        [
            ([], 2),
            ([], 5),
            ([], 1),
            (None, 1),
        ]
    )
    def test_create_plano_entregas_sem_entregas(
        self,
        entregas,
        status
    ):
        """Tenta criar um plano de entregas que não contém entregas.
        Caso o status for 1 - Cancelado, o status deve ser 201 Created.
        """
        input_pe = deepcopy(self.input_pe)
        input_pe["entregas"] = entregas
        input_pe["status"] = status

        response = self.put_plano_entregas(input_pe)

        if isinstance(entregas, list):
            if status != 1 and not entregas:
                assert response.status_code == 422
                detail_message = (
                    "A lista de entregas não pode estar vazia"
                )
                assert_error_message(response, detail_message)
            else:
                assert response.status_code == http_status.HTTP_201_CREATED
        else:
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetPlanoEntregas(BasePETest):
    """Testes para a busca de Planos de Entregas."""

    def test_get_plano_entregas(
        self,
        # pylint: disable=unused-argument
        truncate_pe,  # limpa a base de Planos de Entregas
        example_pe,  # cria um Plano de Entregas de exemplo
    ):
        """Testa a busca de um Plano de Entregas existente.

        Verifica se a API retorna um status 200 OK e se o Plano de Entregas
        retornado é igual ao Plano de Entregas criado.
        """

        response = self.get_plano_entregas(
            self.input_pe["id_plano_entregas"],
            self.user1_credentials["cod_unidade_autorizadora"],
        )
        assert response.status_code == http_status.HTTP_200_OK
        self.assert_equal_plano_entregas(response.json(), self.input_pe)

    def test_get_pe_inexistente(self):
        """Testa a busca de um Plano de Entregas inexistente.

        Verifica se a API retorna um status 404 Not Found e a mensagem
        de erro "Plano de entregas não encontrado".
        """

        response = self.get_plano_entregas(
            "888888888",
            self.user1_credentials["cod_unidade_autorizadora"],
        )
        assert response.status_code == http_status.HTTP_404_NOT_FOUND
        assert response.json().get("detail", None) == "Plano de entregas não encontrado"


class TestCreatePEDuplicateData(BasePETest):
    """Testes para a criação de um Plano de Entregas com dados duplicados."""

    @pytest.mark.parametrize(
        "id_plano_entregas, id_entrega_1, id_entrega_2",
        [
            ("90", "401", "402"),
            ("91", "403", "403"),  # <<<< IGUAIS
            ("92", "404", "404"),  # <<<< IGUAIS
            ("93", "405", "406"),
        ],
    )
    def test_create_pe_duplicate_entrega(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        id_plano_entregas: str,
        id_entrega_1: str,
        id_entrega_2: str,
    ):
        """Testa a criação de um Plano de Entregas com entregas duplicadas.

        Verifica se:
        - a API retorna um erro 422 Unprocessable Entity quando as entregas
          possuem o mesmo id_entrega; e
        - se retorna um status 201 Created quando as entregas possuem ids
          diferentes.
        """

        input_pe = deepcopy(self.input_pe)
        input_pe["id_plano_entregas"] = id_plano_entregas
        input_pe["entregas"][0]["id_entrega"] = id_entrega_1
        input_pe["entregas"][1]["id_entrega"] = id_entrega_2

        response = self.put_plano_entregas(input_pe)
        if id_entrega_1 == id_entrega_2:
            assert response.status_code == 422
            detail_message = "Entregas devem possuir id_entrega diferentes"
            assert any(
                f"Value error, {detail_message}" in error["msg"]
                for error in response.json().get("detail")
            )
        else:
            assert response.status_code == http_status.HTTP_201_CREATED

    def test_create_pe_duplicate_id_plano(
        self,
        truncate_pe,  # pylint: disable=unused-argument
    ):
        """Testa o envio, mais de uma vez, de Planos de Entregas com o
        mesmo id_plano_entregas.

        Verifica se a API:
        - retorna um status 201 Created quando o Plano de Entregas é criado
          pela primeira vez; e
        - um status 200 OK quando o mesmo Plano de Entregas é enviado
          novamente, substituindo o anterior.
        """

        input_pe = deepcopy(self.input_pe)
        response = self.put_plano_entregas(input_pe)
        assert response.status_code == http_status.HTTP_201_CREATED

        response = self.put_plano_entregas(input_pe)
        assert response.status_code == http_status.HTTP_200_OK
        assert response.json().get("detail", None) is None
        self.assert_equal_plano_entregas(response.json(), input_pe)

    def test_create_pe_same_id_plano_different_instituidora(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        user2_credentials: dict,
        header_usr_2: dict,
    ):
        """Testa a criação de Planos de Entregas com o mesmo
        id_plano_entregas, mas com diferentes unidades autorizadoras.

        Uma vez que tratam-se de unidades autorizadoras diferentes, a API
        deve considerá-los como Planos de Entrega diferentes. Por isso,
        deve retornar o status 201 Created em ambos os casos.
        """

        input_pe = deepcopy(self.input_pe)
        response = self.put_plano_entregas(input_pe)
        assert response.status_code == http_status.HTTP_201_CREATED

        input_pe["cod_unidade_autorizadora"] = user2_credentials[
            "cod_unidade_autorizadora"
        ]
        response = self.put_plano_entregas(
            input_pe,
            cod_unidade_autorizadora=user2_credentials["cod_unidade_autorizadora"],
            header_usr=header_usr_2,
        )
        assert response.status_code == http_status.HTTP_201_CREATED
