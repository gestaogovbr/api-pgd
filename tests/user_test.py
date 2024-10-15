"""
Testes relacionados aos métodos de autenticação e usuários.

Disclaimer:
    * header_usr_1: dict is_admin=True
    * header_usr_2: dict is_admin=True
"""

from datetime import datetime
from imaplib import IMAP4
import email
import re
from typing import Generator

from httpx import Client, HTTPStatusError, Response
from fastapi import status
import pytest

from .conftest import get_bearer_token


USERS_TEST: list[dict] = [
    # to create and delete
    {
        "email": "user_test_0@api.com",
        "password": "secret",
        "is_admin": False,
        "disabled": False,
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 1,
        "sistema_gerador": "API PGD CI Test",
    },
    # to get and delete (not created)
    {
        "email": "user_test_1@api.com",
        "password": "secret",
        "is_admin": False,
        "disabled": False,
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 1,
        "sistema_gerador": "API PGD CI Test",
    },
    # to get without one of required fields (email, password, cod_unidade_autorizadora)
    {
        "email": "user_test_2@api.com",
        "password": "secret",
        # "cod_unidade_autorizadora": 1,
    },
    # to create with bad email format. mind that is_admin and disabled are optionals
    {
        "email": "not_a_email",
        "password": "secret",
        # "is_admin": False, # defaults do False
        # "disabled": False, # defaults do False
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 1,
        "sistema_gerador": "API PGD CI Test",
    },
]

TOKEN_IN_MESSAGE = re.compile(r"<code>([^<]+)</code>")

# Classe base de testes


class BaseUserTest:
    """Classe base para testes relacionados a usuários."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        truncate_users,  # pylint: disable=unused-argument
        register_user_1: dict,
        register_user_2: dict,
        header_not_logged_in: dict,
        header_usr_1: dict,
        header_usr_2: dict,
        header_admin: dict,
        client: Client,
    ):
        """Configura o ambiente de testes.

        Args:
            truncate_users (fixture): Trunca a tabela Users.
            register_user_1 (dict): Registra no banco o user 1.
            register_user_2 (dict): Registra no banco o user 2.
            header_not_logged_in (dict): Cabeçalho para um cliente não logado.
            header_usr_1 (dict): Cabeçalho para um cliente logado como o
                user 1.
            header_usr_2 (dict): Cabeçalho para um cliente logado como o
                user 2.
            header_admin (dict): Cabeçalho para um cliente logado como o
                usuário admin.
            client (Client): Uma instância de cliente httpx.
        """
        # pylint: disable=attribute-defined-outside-init
        self.register_user_1 = register_user_1
        self.register_user_2 = register_user_2
        self.header_not_logged_in = header_not_logged_in
        self.header_usr_1 = header_usr_1
        self.header_usr_2 = header_usr_2
        self.header_admin = header_admin
        self.client = client

    def get_bearer_token(self, username: str, password: str) -> str:
        """Get a bearer token for the given username and password.

        Args:
            username (str): The username.
            password (str): The password.

        Returns:
            str: The bearer token.
        """
        response = self.client.post(
            "/token",
            data={
                "username": username,
                "password": password,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def get_users(self, headers: dict) -> Response:
        """Obtém a lista de usuários.

        Args:
            headers (dict): Cabeçalhos HTTP.

        Returns:
            httpx.Response: A resposta da API.
        """
        return self.client.get("/users", headers=headers)

    def get_user(self, email: str, headers: dict) -> Response:
        """Obtém um usuário pelo seu email.

        Args:
            email (str): O email do usuário.
            headers (dict): Cabeçalhos HTTP.

        Returns:
            httpx.Response: A resposta da API.
        """
        return self.client.get(f"/user/{email}", headers=headers)

    def create_or_update_user(self, email: str, data: dict, headers: dict) -> Response:
        """Cria ou atualiza um usuário.

        Args:
            email (str): O email do usuário.
            data (dict): Os dados do usuário.
            headers (dict): Cabeçalhos HTTP.

        Returns:
            httpx.Response: A resposta da API.
        """
        return self.client.put(
            f"/user/{email}",
            headers=headers,
            json=data,
        )


# post /token


class TestUserAuthentication(BaseUserTest):
    """Testes relacionados à autenticação de usuários."""

    def test_authenticate(self, header_usr_1: dict):
        """Verifica se o token de autenticação é gerado corretamente.

        Args:
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
        """
        token = header_usr_1.get("Authorization")
        assert isinstance(token, str)

    def test_attempt_log_in_disabled_user(
        self,
        truncate_users,  # pylint: disable=unused-argument
        register_user_1: dict,  # pylint: disable=unused-argument
        header_admin: dict,  # pylint: disable=unused-argument
        client: Client,
        user1_credentials: dict,
    ):
        """Cria um novo usuário, o desabilita e tenta logar com esse usuário.

        Args:
            truncate_users (fixture): Trunca a tabela de usuários.
            register_user_1 (dict): Dados do usuário 1.
            header_admin (dict): Cabeçalhos HTTP para o usuário admin.
            client (Client): Uma instância do cliente HTTPX.
            user1_credentials (dict): Credenciais do usuário 1.
        """
        user1_data = user1_credentials.copy()

        # update user 1 and disable it
        user1_data["disabled"] = True
        response = client.put(
            f"/user/{user1_data['email']}",
            headers=header_admin,
            json=user1_data,
        )
        assert response.status_code == status.HTTP_200_OK

        # try to log in as user 1
        with pytest.raises(HTTPStatusError):
            self.get_bearer_token(
                username=user1_data["email"], password=user1_data["password"]
            )


# get /users


class TestGetUsers(BaseUserTest):
    """Testes relacionados à obtenção de usuários."""

    def test_get_all_users_not_logged_in(self, header_not_logged_in: dict):
        """Testa a obtenção de todos os usuários sem estar logado.

        Args:
            header_not_logged_in (dict): Cabeçalhos HTTP para um usuário
                não logado.
        """
        response = self.get_users(header_not_logged_in)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_all_users_logged_in_not_admin(
        self,
        truncate_users,  # pylint: disable=unused-argument
        header_usr_2: dict,
    ):
        """Testa a obtenção de todos os usuários por um usuário logado,
        mas não admin.

        Args:
            truncate_users (fixture): Trunca a tabela de usuários.
            header_usr_2 (dict): Cabeçalhos HTTP para o usuário 2.
        """
        response = self.get_users(header_usr_2)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_users_logged_in_admin(self, header_usr_1: dict):
        """Testa a obtenção de todos os usuários por um usuário admin.

        Args:
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1 (admin).
        """
        response = self.get_users(header_usr_1)
        assert response.status_code == status.HTTP_200_OK


# get /user


class TestGetSingleUser(BaseUserTest):
    """Testes relacionados à obtenção de um único usuário."""

    def test_get_user_not_logged_in(self, header_not_logged_in: dict):
        """Testa a obtenção de um usuário sem estar logado.

        Args:
            header_not_logged_in (dict): Cabeçalhos HTTP para um usuário não logado.
        """
        response = self.get_user("foo@oi.com", header_not_logged_in)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_logged_in_not_admin(
        self, user2_credentials: dict, header_usr_2: dict  # user is_admin=False
    ):
        """Testa a obtenção de um usuário por um usuário logado, mas não admin.

        Args:
            user2_credentials (dict): Credenciais do usuário 2.
            header_usr_2 (dict): Cabeçalhos HTTP para o usuário 2.
        """
        response = self.get_user(user2_credentials["email"], header_usr_2)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_as_admin(
        self, user1_credentials: dict, header_usr_1: dict  # user is_admin=True
    ):
        """Testa a obtenção de um usuário por um usuário admin.

        Args:
            user1_credentials (dict): Credenciais do usuário 1.
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
        """
        response = self.get_user(user1_credentials["email"], header_usr_1)
        assert response.status_code == status.HTTP_200_OK

    def test_get_user_not_exists(self, header_usr_1: dict):  # user is_admin=True
        """Testa a obtenção de um usuário que não existe.

        Args:
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
        """
        response = self.get_user(USERS_TEST[1]["email"], header_usr_1)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_self_logged_in(
        self,
        truncate_users,  # pylint: disable=unused-argument
        user1_credentials: dict,
        header_usr_1: dict,  # user is_admin=True
    ):
        """Testa a obtenção de um usuário por ele mesmo.

        Args:
            truncate_users (fixture): Trunca a tabela de usuários.
            user1_credentials (dict): Credenciais do usuário 1.
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
        """
        response = self.get_user(user1_credentials["email"], header_usr_1)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get("email", None) == user1_credentials["email"]
        assert data.get("is_admin", None) == user1_credentials["is_admin"]
        assert data.get("disabled", None) == user1_credentials["disabled"]
        assert data.get("origem_unidade", None) == user1_credentials["origem_unidade"]
        assert (
            data.get("cod_unidade_autorizadora", None)
            == user1_credentials["cod_unidade_autorizadora"]
        )


# create /user


class TestCreateUser(BaseUserTest):
    """Testes relacionados à criação de usuários."""

    def test_create_user_not_logged_in(self, header_not_logged_in: dict):
        """Testa a criação de um usuário sem estar logado.

        Args:
            header_not_logged_in (dict): Cabeçalhos HTTP para um usuário não logado.
        """
        response = self.create_or_update_user(
            USERS_TEST[0]["email"],
            USERS_TEST[0],
            header_not_logged_in,
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_user_logged_in_not_admin(
        self, header_usr_2: dict
    ):  # user is_admin=False
        """Testa a criação de um usuário por um usuário logado, mas não admin.

        Args:
            header_usr_2 (dict): Cabeçalhos HTTP para o usuário 2.
        """
        response = self.create_or_update_user(
            USERS_TEST[0]["email"],
            USERS_TEST[0],
            header_usr_2,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_logged_in_admin(
        self, header_usr_1: dict
    ):  # user is_admin=True
        """Testa a criação de um usuário por um usuário admin.

        Args:
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
        """
        response = self.create_or_update_user(
            USERS_TEST[0]["email"],
            USERS_TEST[0],
            header_usr_1,
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_user_without_required_fields(
        self, header_usr_1: dict
    ):  # user is_admin=True
        """Testa a criação de um usuário sem preencher campos obrigatórios.

        Args:
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
        """
        response = self.create_or_update_user(
            USERS_TEST[2]["email"],
            USERS_TEST[2],
            header_usr_1,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_bad_email_format(
        self, header_usr_1: dict
    ):  # user is_admin=True
        """Testa a criação de um usuário com formato de email inválido.

        Args:
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
        """
        response = self.create_or_update_user(
            USERS_TEST[3]["email"],
            USERS_TEST[3],
            header_usr_1,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# update /user


class TestUpdateUser(BaseUserTest):
    """Testes relacionados à atualização de usuários."""

    def test_update_user(self, header_usr_1: dict):  # user is_admin=True
        """Testa a atualização de um usuário.

        Args:
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
        """
        # get
        r_1 = self.get_user(USERS_TEST[0]["email"], header_usr_1)
        data_before = r_1.json()

        # update
        new_data = data_before
        new_data["cod_unidade_autorizadora"] = 99
        new_data["password"] = "new_secret"
        r_2 = self.create_or_update_user(USERS_TEST[0]["email"], new_data, header_usr_1)
        assert r_2.status_code == status.HTTP_200_OK

        # get new value
        r_3 = self.get_user(USERS_TEST[0]["email"], header_usr_1)
        data_after = r_3.json()

        assert data_before.get("cod_unidade_autorizadora", None) == data_after.get(
            "cod_unidade_autorizadora", None
        )


# forgot/reset password


class TestForgotPassword(BaseUserTest):
    """Testes relacionados à funcionalidade de esquecimento de senha."""

    def get_all_mailbox_messages(
        self,
        host: str = "smtp4dev",
        user: str = "smtp4dev",
        password: str = "",
    ) -> Generator[email.message.Message, None, None]:
        """Obtém as mensagens da caixa de entrada.

        Args:
            host (str, optional): Host da conexão IMAP. Padrão é "smtp4dev".
            user (str, optional): Usuário da conexão IMAP. Padrão é "smtp4dev".
            password (str, optional): Senha da conexão IMAP. Padrão é "".

        Raises:
            ValueError: se não for possível acessar a caixa de entrada.

        Yields:
            Iterator[email.message.Message]: cada mensagem encontrada na caixa de entrada.
        """
        with IMAP4(host=host, port=143) as connection:
            connection.login(user, password)
            connection.enable("UTF8=ACCEPT")
            query_status, inbox = connection.select(readonly=True)
            if query_status != "OK":
                raise ValueError("Acesso à caixa de entrada de email falhou.")
            message_count = int(inbox[0].decode("utf-8"))
            for message_index in range(message_count + 1):
                query_status, response = connection.fetch(
                    str(message_index), "(RFC822)"
                )
                for item in response:
                    if isinstance(item, tuple):
                        yield email.message_from_bytes(item[1])

    def get_latest_message_uid(self, messages: dict[int, email.message.Message]) -> str:
        """Obtém o UID da última mensagem da caixa de entrada.

        Args:
            messages (dict[int,email.message.Message]): um dicionário contendo
                os UIDs das mensagens como chaves e os objetos das mensagens como valores,
                representando todas as mensagens na caixa de entrada.

        Returns:
            str: o UID da última mensagem.
        """
        return max(
            (
                (datetime.strptime(message["date"], "%a, %d %b %Y %H:%M:%S %z"), index)
                for index, message in messages.items()
            )
        )[1]

    def get_message_body(
        self,
        uid: int,
        host: str = "smtp4dev",
        user: str = "smtp4dev",
        password: str = "",
    ) -> str:
        """Obtém o corpo da mensagem com o UID fornecido do servidor IMAP.

        Args:
            uid (int): o UID da mensagem.
            host (str, optional): Host da conexão IMAP. Padrão é "smtp4dev".
            user (str, optional): Usuário da conexão IMAP. Padrão é "smtp4dev".
            password (str, optional): Senha da conexão IMAP. Padrão é "".

        Raises:
            ValueError: se não for possível acessar a caixa de entrada.

        Returns:
            str: o corpo da mensagem.
        """
        with IMAP4(host=host, port=143) as connection:
            connection.login(user, password)
            connection.enable("UTF8=ACCEPT")
            query_status, _ = connection.select(readonly=True)
            if query_status != "OK":
                raise ValueError("Acesso à caixa de entrada de email falhou.")
            query_status, response = connection.fetch(str(uid), "(RFC822)")
            message = email.message_from_bytes(response[0][1])
            content = bytes(
                [
                    part
                    for part in message.walk()
                    if part.get_content_type() == "text/html"
                ][0].get_payload(decode=True)
            )
            return content.decode("utf-8")

    def get_token_from_content(self, content: str) -> str:
        """Get the token from the email content.

        Args:
            content (str): content of email.

        Raises:
            ValueError: if no token is found in the email.

        Returns:
            str: the access token.
        """
        match = TOKEN_IN_MESSAGE.search(content)
        if match:
            return match.group(1)
        raise ValueError("Message contains no token.")

    def get_token_from_email(
        self,
        host: str = "smtp4dev",
        user: str = "smtp4dev",
        password: str = "",
    ) -> str:
        """Access the mailbox and get the token from the email.

        Args:
            host (str, optional): IMAP connection host. Defaults to "localhost".
            user (str, optional): IMAP connection user name. Defaults to "smtp4dev".
            password (str, optional): IMAP connection password. Defaults to "".

        Returns:
            str: the access token.
        """
        messages = dict(
            enumerate(self.get_all_mailbox_messages(host, user, password), start=1)
        )
        latest_message = int(self.get_latest_message_uid(messages))
        return self.get_token_from_content(
            self.get_message_body(uid=latest_message, host=host)
        )

    def test_forgot_password(
        self,
        user1_credentials: dict,
    ):
        """Tests the forgot and reset password functionality."""
        # use the forgot_password endpoint to send an email
        response = self.client.post(
            f"/user/forgot_password/{user1_credentials['email']}",
            headers=self.header_usr_1,
        )
        assert response.status_code == status.HTTP_200_OK

        # get the token from the email
        access_token = self.get_token_from_email(host="smtp4dev")

        # reset the password to a new password using the received token
        new_password = "new_password_for_test"
        response = self.client.get(
            "/user/reset_password/",
            params={"access_token": access_token, "password": new_password},
        )
        assert response.status_code == status.HTTP_200_OK

        # test if the old credentials no longer work
        response = self.client.post(
            "/token",
            data={
                "username": user1_credentials["email"],
                "password": user1_credentials["password"],
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # test if the new credentials work
        response = self.client.post(
            "/token",
            data={
                "username": user1_credentials["email"],
                "password": new_password,
            },
        )
        assert response.status_code == status.HTTP_200_OK
