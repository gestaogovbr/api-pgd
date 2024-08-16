"""
Testes relacionados aos status de participantes.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import status
from httpx import Client, Response

import pytest

# Relação de campos obrigatórios para testar sua ausência:
FIELDS_PARTICIPANTES = {
    "optional": tuple(),  # nenhum campo é opcional
    "mandatory": (
        ["origem_unidade"],
        ["cod_unidade_autorizadora"],
        ["cod_unidade_lotacao"],
        ["cpf"],
        ["matricula_siape"],
        ["cod_unidade_instituidora"],
        ["situacao"],
        ["modalidade_execucao"],
        ["data_assinatura_tcr"],
    ),
}

# Classe base de testes


class BaseParticipanteTest:
    """Classe base para testes de Participantes."""

    # pylint: disable=too-many-arguments
    @pytest.fixture(autouse=True)
    def setup(
        self,
        truncate_participantes,  # pylint: disable=unused-argument
        input_part: dict,
        user1_credentials: dict,
        header_usr_1: dict,
        header_usr_2: dict,
        header_admin: dict,
        admin_credentials: dict,
        client: Client,
    ):
        """Configurar o ambiente de teste.

        Args:
                Participantes.
            input_part (dict): Dados usados para criar um Participante.
            user1_credentials (dict): Credenciais do usuário 1.
            header_usr_2 (dict): Cabeçalhos HTTP para o usuário 2.
            header_admin (dict): Cabeçalhos HTTP para o usuário admin.
            admin_credentials (dict): Credenciais do usuário admin.
            client (Client): Uma instância do cliente HTTPX.
        """
        # pylint: disable=attribute-defined-outside-init
        self.input_part = input_part
        self.user1_credentials = user1_credentials
        self.header_usr_1 = header_usr_1
        self.header_usr_2 = header_usr_2
        self.header_admin = header_admin
        self.admin_credentials = admin_credentials
        self.client = client

    @staticmethod
    def parse_datetimes(data: dict) -> dict:
        """Parse datetimes from the data."""
        if isinstance(data["data_assinatura_tcr"], str):
            data["data_assinatura_tcr"] = datetime.fromisoformat(
                data["data_assinatura_tcr"]
            )
        return data

    @staticmethod
    def remove_null_optional_fields(data: dict) -> dict:
        """Remove fields that are None from the data."""
        if not isinstance(data, dict):
            print(f"data: {data}")
            print(f"type: {type(data)}")
            raise ValueError("Data must be a dict")
        for fields in FIELDS_PARTICIPANTES["optional"]:
            for field in fields:
                if field in data and data[field] is None:
                    del data[field]
        return data

    @staticmethod
    def assert_equal_participante(participante_1: dict, participante_2: dict):
        """Verifica a igualdade de dois participantes, considerando
        apenas os campos obrigatórios.
        """
        assert BaseParticipanteTest.parse_datetimes(
            BaseParticipanteTest.remove_null_optional_fields(participante_1.copy())
        ) == BaseParticipanteTest.parse_datetimes(
            BaseParticipanteTest.remove_null_optional_fields(participante_2.copy())
        )

    def create_participante(
        self,
        input_part: dict,
        cod_unidade_autorizadora: Optional[int] = None,
        cod_unidade_lotacao: Optional[int] = None,
        matricula_siape: Optional[str] = None,
        header_usr: Optional[dict] = None,
    ) -> Response:
        """Criar um Participante.

        Args:
            input_part (dict): O dicionário de entrada do Participante.
            cod_unidade_autorizadora (int): O ID da unidade autorizadora.
            cod_unidade_lotacao (int): O ID da unidade de lotação.
            matricula_siape (str): A matrícula SIAPE do Participante.
            header_usr (dict): Cabeçalhos HTTP para o usuário.

        Returns:
            httpx.Response: A resposta da API.
        """
        if cod_unidade_autorizadora is None:
            cod_unidade_autorizadora = input_part["cod_unidade_autorizadora"]
        if cod_unidade_lotacao is None:
            cod_unidade_lotacao = input_part["cod_unidade_lotacao"]
        if matricula_siape is None:
            matricula_siape = input_part["matricula_siape"]
        if header_usr is None:
            header_usr = self.header_usr_1

        response = self.client.put(
            (
                f"/organizacao/SIAPE/{cod_unidade_autorizadora}"
                f"/{cod_unidade_lotacao}/participante/{matricula_siape}"
            ),
            json=input_part,
            headers=header_usr,
        )
        return response

    def get_participante(
        self,
        matricula_siape: str,
        cod_unidade_autorizadora: int,
        cod_unidade_lotacao: int,
        header_usr: Optional[dict] = None,
    ) -> Response:
        """Obter um Participante.

        Args:
            matricula_siape (str): A matrícula SIAPE do Participante.
            cod_unidade_autorizadora (int): O ID da unidade autorizadora.
            cod_unidade_lotacao (int): O ID da unidade de lotação.
            header_usr (dict): Cabeçalhos HTTP para o usuário.

        Returns:
            httpx.Response: A resposta da API.
        """
        if header_usr is None:
            header_usr = self.header_usr_1
        response = self.client.get(
            f"/organizacao/SIAPE/{cod_unidade_autorizadora}"
            f"/{cod_unidade_lotacao}"
            f"/participante/{matricula_siape}",
            headers=header_usr,
        )
        return response


class TestCreateParticipante(BaseParticipanteTest):
    """Testes para criação de Participante."""

    def test_create_participante_complete(self):
        """Cria um novo Participante, em uma unidade na qual o usuário
        está autorizado, contendo todos os dados necessários.
        """
        response = self.create_participante(
            self.input_part,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json().get("detail", None) is None
        self.assert_equal_participante(response.json(), self.input_part)

    def test_create_participante_in_unauthorized_unit(self):
        """Tenta submeter um participante em outra unidade autorizadora
        (user não é admin)
        """
        response = self.create_participante(
            self.input_part,
            cod_unidade_autorizadora=3,  # unidade diferente
            header_usr=self.header_usr_2,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        detail_msg = "Usuário não tem permissão na cod_unidade_autorizadora informada"
        assert response.json().get("detail", None) == detail_msg

    def test_create_participante_in_other_unit_as_admin(self):
        """Testa, usando usuário admin, a submissão de um participante em outra
        unidade autorizadora
        """
        self.input_part["cod_unidade_autorizadora"] = 3  # unidade diferente
        self.input_part["cod_unidade_lotacao"] = 30  # unidade diferente

        response = self.client.get(
            f"/user/{self.admin_credentials['username']}",
            headers=self.header_admin,
        )

        # Verifica se o usuário é admin e se está em outra unidade
        assert response.status_code == status.HTTP_200_OK
        admin_data = response.json()
        assert (
            admin_data.get("cod_unidade_autorizadora", None)
            != self.input_part["cod_unidade_autorizadora"]
        )
        assert admin_data.get("is_admin", None) is True

        response = self.create_participante(
            self.input_part,
            header_usr=self.header_admin,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json().get("detail", None) is None
        self.assert_equal_participante(response.json(), self.input_part)


class TestUpdateParticipante(BaseParticipanteTest):
    """Testes para atualização de um Participante."""

    def test_update_participante_with_existing_pt(
        self,
        # pylint: disable=unused-argument
        example_part: dict,
        example_pt: dict,
    ):
        """Atualiza um participante existente, sendo que o participante já
        possui um Plano de Trabalho a ele associado.
        """
        input_part = self.input_part.copy()
        response = self.create_participante(input_part)
        assert response.status_code == status.HTTP_200_OK

    def test_update_participante(
        self,
    ):
        """Atualiza um participante existente."""
        input_part = self.input_part.copy()
        response = self.create_participante(input_part)
        assert response.status_code == status.HTTP_201_CREATED

        input_part["modalidade_execucao"] = 2
        response = self.create_participante(input_part)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["modalidade_execucao"] == 2

    @pytest.mark.parametrize(
        (
            "cod_unidade_autorizadora_1, cod_unidade_autorizadora_2, "
            "cod_unidade_lotacao_1, cod_unidade_lotacao_2, "
            "matricula_siape_1, matricula_siape_2"
        ),
        [
            # mesmas unidades, mesma matrícula SIAPE
            (1, 1, 10, 10, "1237654", "1237654"),
            # unidades autorizadoras diferentes, mesma matrícula SIAPE
            (1, 2, 10, 20, "1237654", "1237654"),
            # unidades de lotação diferentes, mesma matrícula SIAPE
            (1, 1, 10, 11, "1237654", "1237654"),
            # mesma unidade, matrículas diferentes
            (1, 1, 10, 10, "1237654", "1230054"),
            # unidades diferentes, matrículas diferentes
            (1, 2, 10, 20, "1237654", "1230054"),
        ],
    )
    def test_update_participante_duplicate_matricula(
        self,
        cod_unidade_autorizadora_1: int,
        cod_unidade_autorizadora_2: int,
        cod_unidade_lotacao_1: int,
        cod_unidade_lotacao_2: int,
        matricula_siape_1: str,
        matricula_siape_2: str,
    ):
        """
        Testa o envio de um mesmo participante com a mesma matrícula SIAPE.
        O comportamento do segundo envio será testado conforme o caso.

        Sendo a mesma matrícula na mesma unidade autorizadora e de lotação,
        o registro será atualizado e retornará o código HTTP 200 Ok.
        Se a unidade e/ou a matrícula forem diferentes, entende-se que será
        criado um novo registro e será retornado o código HTTP 201 Created.
        """
        input_part = self.input_part.copy()
        input_part["cod_unidade_autorizadora"] = cod_unidade_autorizadora_1
        input_part["cod_unidade_lotacao"] = cod_unidade_lotacao_1
        input_part["matricula_siape"] = matricula_siape_1
        response = self.create_participante(
            input_part,
            cod_unidade_autorizadora=cod_unidade_autorizadora_1,
            cod_unidade_lotacao=cod_unidade_lotacao_1,
            matricula_siape=matricula_siape_1,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json().get("detail", None) is None
        self.assert_equal_participante(response.json(), input_part)

        # ajusta o header para que tenha permissão de escrever naquele
        # cod_unidade_autorizadora
        if (
            cod_unidade_autorizadora_2
            == self.user1_credentials["cod_unidade_autorizadora"]
        ):
            header_usr = self.header_usr_1
        else:
            header_usr = self.header_usr_2
        input_part["cod_unidade_autorizadora"] = cod_unidade_autorizadora_2
        input_part["cod_unidade_lotacao"] = cod_unidade_lotacao_2
        input_part["matricula_siape"] = matricula_siape_2
        response = self.create_participante(
            input_part,
            cod_unidade_autorizadora=cod_unidade_autorizadora_2,
            cod_unidade_lotacao=cod_unidade_lotacao_2,
            matricula_siape=matricula_siape_2,
            header_usr=header_usr,
        )

        if (
            (cod_unidade_autorizadora_1 == cod_unidade_autorizadora_2)
            and (cod_unidade_lotacao_1 == cod_unidade_lotacao_2)
            and (matricula_siape_1 == matricula_siape_2)
        ):
            # tudo é igual, está atualizando o mesmo participante
            assert response.status_code == status.HTTP_200_OK
        else:
            # algo é diferente, está criando um novo participante
            assert response.status_code == status.HTTP_201_CREATED
        assert response.json().get("detail", None) is None
        self.assert_equal_participante(response.json(), input_part)


class TestCreateParticipanteInconsistentURLData(BaseParticipanteTest):
    """Testa situações em que os dados da URL diferem do informado no JSON."""

    def test_create_participante_inconsistent(
        self,
    ):
        """Tenta submeter participante inconsistente (URL difere do JSON)"""
        nova_matricula = "3311776"
        response = self.create_participante(
            input_part=self.input_part,
            matricula_siape=nova_matricula,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = "Parâmetro matricula_siape na URL e no JSON devem ser iguais"
        assert response.json().get("detail", None) == detail_msg


class TestCreateParticipanteFieldValidation(BaseParticipanteTest):
    """Testes para verificar as validações de campos do Participante."""

    @pytest.mark.parametrize(
        "matricula_siape",
        [
            ("12345678"),
            ("0000000"),
            ("9999999"),
            ("123456"),
            ("-123456"),
            ("abcdefg"),
        ],
    )
    def test_create_participante_invalid_matricula_siape(self, matricula_siape: str):
        """Tenta submeter um participante com matricula_siape inválida."""
        input_part = self.input_part.copy()
        input_part["matricula_siape"] = matricula_siape
        response = self.create_participante(
            input_part,
            matricula_siape=input_part["matricula_siape"],
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_messages = [
            "Matricula SIAPE deve ser numérica.",
            "Matrícula SIAPE deve ter 7 dígitos.",
            "Matricula SIAPE inválida.",
        ]
        received_error = response.json().get("detail")
        if isinstance(received_error, str):
            assert any(message in received_error for message in detail_messages)
        else:
            assert any(
                f"Value error, {message}" in error["msg"]
                for message in detail_messages
                for error in received_error
            )

    @pytest.mark.parametrize(
        "cpf_participante",
        [
            ("11111111111"),
            ("22222222222"),
            ("33333333333"),
            ("44444444444"),
            ("04811556435"),
            ("444444444"),
            ("4811556437"),
        ],
    )
    def test_create_participante_invalid_cpf(self, cpf_participante: str):
        """Tenta submeter um participante com cpf inválido."""
        input_part = self.input_part.copy()
        input_part["cpf"] = cpf_participante
        response = self.create_participante(input_part)
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

    @pytest.mark.parametrize(
        "missing_fields", enumerate(FIELDS_PARTICIPANTES["mandatory"])
    )
    def test_create_participante_missing_mandatory_fields(self, missing_fields: list):
        """Tenta submeter participantes faltando campos obrigatórios"""
        input_part = self.input_part.copy()
        cod_unidade_lotacao = input_part["cod_unidade_lotacao"]
        matricula_siape = input_part["matricula_siape"]
        offset, field_list = missing_fields
        for field in field_list:
            del input_part[field]

        input_part["matricula_siape"] = (
            f"{1800000 + offset}"  # precisa ser um novo participante
        )
        response = self.create_participante(
            input_part,
            cod_unidade_autorizadora=self.user1_credentials["cod_unidade_autorizadora"],
            cod_unidade_lotacao=cod_unidade_lotacao,
            matricula_siape=matricula_siape,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "situacao",
        [
            (3),
            (-1),
        ],
    )
    def test_create_participante_invalid_status(self, situacao: int):
        """Tenta criar um participante com flag participante
        com valor inválido."""
        input_part = self.input_part.copy()
        input_part["situacao"] = situacao
        response = self.create_participante(input_part)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_messages = "Valor do campo 'situacao' inválido; permitido: 0, 1"
        assert any(
            f"Value error, {message}" in error["msg"]
            for message in detail_messages
            for error in response.json().get("detail")
        )

    @pytest.mark.parametrize("modalidade_execucao", [(0), (-1), (6)])
    def test_create_participante_invalid_modalidade_execucao(
        self, modalidade_execucao: int
    ):
        """Tenta submeter um participante com modalidade de execução inválida"""
        input_part = self.input_part.copy()
        input_part["modalidade_execucao"] = modalidade_execucao
        response = self.create_participante(input_part)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_messages = "Modalidade de execução inválida; permitido: 1, 2, 3, 4, 5"
        assert any(
            f"Value error, {message}" in error["msg"]
            for message in detail_messages
            for error in response.json().get("detail")
        )


class TestGetParticipante(BaseParticipanteTest):
    """Testes para a leitura de Participantes."""

    def test_get_participante(self, example_part):  # pylint: disable=unused-argument
        """Tenta ler os dados de um participante pelo cpf."""
        response = self.get_participante(
            matricula_siape=self.input_part["matricula_siape"],
            cod_unidade_autorizadora=self.input_part["cod_unidade_autorizadora"],
            cod_unidade_lotacao=self.input_part["cod_unidade_lotacao"],
        )
        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_participante(response.json(), self.input_part)

    def test_get_participante_not_found(self):
        """Tenta consultar um participante que não existe na base de dados."""
        response = self.get_participante(
            matricula_siape=3311776,
            cod_unidade_autorizadora=self.user1_credentials["cod_unidade_autorizadora"],
            cod_unidade_lotacao=1,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json().get("detail", None) == "Participante não encontrado"

    def test_get_participante_in_different_unit(
        self, example_part_unidade_3: dict  # pylint: disable=unused-argument
    ):
        """Testa ler um participante em outra unidade autorizadora
        (usuário não é admin)"""
        input_part = self.input_part.copy()
        input_part["cod_unidade_autorizadora"] = 3

        response = self.get_participante(
            matricula_siape=input_part["matricula_siape"],
            cod_unidade_autorizadora=input_part["cod_unidade_autorizadora"],
            cod_unidade_lotacao=input_part["cod_unidade_lotacao"],
            header_usr=self.header_usr_2,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        detail_msg = "Usuário não tem permissão na cod_unidade_autorizadora informada"
        assert response.json().get("detail", None) == detail_msg

    def test_get_participante_in_different_unit_as_admin(
        self, example_part_unidade_3: dict  # pylint: disable=unused-argument
    ):
        """Testa ler um participante em outra unidade autorizadora
        (usuário é admin)"""
        input_part = self.input_part.copy()
        input_part["cod_unidade_autorizadora"] = 3

        response = self.get_participante(
            matricula_siape=input_part["matricula_siape"],
            cod_unidade_autorizadora=input_part["cod_unidade_autorizadora"],
            cod_unidade_lotacao=input_part["cod_unidade_lotacao"],
            header_usr=self.header_admin,
        )
        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_participante(response.json(), input_part)


class TestCreateParticipanteDateValidation(BaseParticipanteTest):
    """Testes de validação de data durante a criação de um Participante."""

    def test_create_participante_invalid_data_assinatura_tcr(self):
        """Tenta criar um participante com data futura de assinatura do TCR."""
        input_part = self.input_part.copy()
        # data de amanhã
        input_part["data_assinatura_tcr"] = (
            date.today() + timedelta(days=1)
        ).isoformat()
        response = self.create_participante(input_part)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_messages = "Input should be in the past"
        assert any(
            message in error["msg"]
            for message in detail_messages
            for error in response.json().get("detail")
        )

    @pytest.mark.parametrize(
        "timezone_utc",
        [
            None,  # sem fuso horário (timezone-naïve)
            0,  # horário de Greenwich
            -3,  # hora de Brasília
            -5,  # horário de Rio Branco
        ],
    )
    def test_create_participante_data_assinatura_tcr_timezone(
        self, timezone_utc: Optional[int]
    ):
        """Tenta criar um participante com data de assinatura do TCR em
        diversos fuso-horários (chamado "timezone-aware"), ou sem
        definição de fuso-horário (chamado "timezone-naïve")."""
        input_part = self.input_part.copy()
        input_part["data_assinatura_tcr"] = (
            datetime.now(  # horário de agora
                **(
                    {"tz": timezone(timedelta(hours=timezone_utc))}  # com tz
                    if timezone_utc is not None
                    else {}  # sem tz
                )
            )
            - timedelta(days=1)
        ).isoformat()
        response = self.create_participante(input_part)

        assert response.status_code == status.HTTP_201_CREATED
