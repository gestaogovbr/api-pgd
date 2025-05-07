"""
Funções auxiliares e fixtures dos testes.
"""

from copy import deepcopy
import os
import sys
import json
from typing import Generator, Optional
import asyncio

import httpx
from fastapi import status
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crud import (
    truncate_plano_entregas,
    truncate_plano_trabalho,
    truncate_participante,
    truncate_user,
)
from crud_auth import init_user_admin
from api import app

USERS_CREDENTIALS = [
    {
        "username": "test1@api.com",
        "email": "test1@api.com",
        "password": "secret1",
        "is_admin": True,
        "disabled": False,
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 1,
        "sistema_gerador": "API PGD CI Tests",
    },
    {
        "username": "test2@api.com",
        "email": "test2@api.com",
        "password": "secret2",
        # "is_admin": False, # defaults set to False
        # "disabled": False, # defaults set to False
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 2,
        "sistema_gerador": "API PGD CI Tests",
    },
]

API_PGD_ADMIN_USER = os.environ.get("API_PGD_ADMIN_USER")
API_PGD_ADMIN_PASSWORD = os.environ.get("API_PGD_ADMIN_PASSWORD")

API_BASE_URL = "http://localhost:5057"

TEST_USER_AGENT = "API PGD CI Test (+https://github.com/gestaogovbr/api-pgd)"

MAX_INT = (2**31) - 1
MAX_BIGINT = (2**63) - 1


def get_bearer_token(username: str, password: str) -> str:
    """Login on api-pgd and returns token to next authenticated calls.

    Args:
        username (str): username as email (foo@oi.com)
        password (str): user password

    Returns:
        str: Bearer token of authenticated user
    """

    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "username": username,
        "password": password,
    }

    with httpx.Client() as client:
        response = client.post(f"{API_BASE_URL}/token", headers=headers, data=data)
        response.raise_for_status()

        return response.json()["access_token"]


def prepare_header(username: Optional[str], password: Optional[str]) -> dict:
    """Prepara o cabeçalho para ser utilizado em requisições."""
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": TEST_USER_AGENT,
    }

    if username and password:
        user_token = get_bearer_token(username, password)
        headers["Authorization"] = f"Bearer {user_token}"

    return headers


def get_all_users(username: str, password: str) -> list[str]:
    """Get all usersnames (emails) registered on api-pgd database.

    Args:
        username (str): username as email (foo@oi.com)
        password (str): user password

    Returns:
        list[str]: list of usernames (emails) registered on api-pgd
            database
    """

    headers = prepare_header(username, password)
    response = httpx.get(f"{API_BASE_URL}/users", headers=headers)
    response.raise_for_status()
    users_email = [user["email"] for user in response.json()]

    return users_email


def delete_user(username: str, password: str, del_user_email: str) -> httpx.Response:
    """Delete user from api-pgd database.

    Args:
        username (str): username as email (foo@oi.com)
        password (str): user password
        del_user_email (str): email (username) of the user to be deleted

    Returns:
        httpx.Response: httpx.Response
    """

    headers = prepare_header(username, password)
    response = httpx.delete(f"{API_BASE_URL}/user/{del_user_email}", headers=headers)
    response.raise_for_status()

    return response


def create_user(username: str, password: str, new_user: dict) -> httpx.Response:
    """Cria um novo usuário usando a API.

    Args:
        username (str): O nome de usuário (email) do usuário.
        password (str): A senha do usuário.
        new_user (dict): Um dicionário contendo as informações do novo usuário
            a ser criado, exceto o nome de usuário (email).

    Returns:
        httpx.Response: A resposta HTTP da requisição de criação do usuário.
    """
    headers = prepare_header(username, password)
    new_user_pop = {key: value for key, value in new_user.items() if key != "username"}
    response = httpx.put(
        f"{API_BASE_URL}/user/{new_user['email']}", headers=headers, json=new_user_pop
    )
    response.raise_for_status()

    return response


# Fixtures


@pytest.fixture(scope="session", name="truncate_users")
def fixture_truncate_users(admin_credentials: dict):  # pylint: disable=unused-argument
    """Trunca a tabela de usuários e inicializa o usuário administrador."""
    truncate_user()
    asyncio.get_event_loop().run_until_complete(init_user_admin())


@pytest.fixture(scope="session", name="register_user_1")
def fixture_register_user_1(
    truncate_users,  # pylint: disable=unused-argument
    user1_credentials: dict,
    admin_credentials: dict,
) -> httpx.Response:
    """Cria um novo usuário de teste 1 usando a API.

    Returns:
        httpx.Response: A resposta HTTP da requisição de criação do usuário.
    """
    response = create_user(
        admin_credentials["username"], admin_credentials["password"], user1_credentials
    )
    response.raise_for_status()

    return response


@pytest.fixture(scope="session", name="register_user_2")
def fixture_register_user_2(
    truncate_users,  # pylint: disable=unused-argument
    user2_credentials: dict,
    admin_credentials: dict,
) -> httpx.Response:
    """Cria um novo usuário de teste 2 usando a API.

    Retorna:
        httpx.Response: A resposta HTTP da requisição de criação do usuário.
    """
    response = create_user(
        admin_credentials["username"], admin_credentials["password"], user2_credentials
    )
    response.raise_for_status()

    return response


@pytest.fixture()
def non_existing_user_credentials() -> dict:
    """Retorna pseudo credenciais de um usuário não existente."""
    return {"email": "naoexiste@naoexiste.com", "password": "inexistente"}


@pytest.fixture()
def disabled_user_1(
    header_admin: dict,  # pylint: disable=unused-argument
    user1_credentials: dict,
    client: TestClient,
) -> Generator[dict, None, None]:
    """Desabilitar o usuário 1, fornecer seus dados e retornar ao estado
    anterior."""
    # update user 1 and disable it
    user1_data = deepcopy(user1_credentials)
    user1_data["disabled"] = True
    response = client.put(
        f"/user/{user1_data['email']}",
        headers=header_admin,
        json=user1_data,
    )
    assert response.status_code == status.HTTP_200_OK

    yield user1_data

    response = client.put(
        f"/user/{user1_credentials['email']}",
        headers=header_admin,
        json=user1_credentials,
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.fixture(scope="session")
def header_not_logged_in() -> dict:
    """Cabeçalho HTTP para requisições sem autenticação.

    Returns:
        dict: Um dicionário contendo os cabeçalhos HTTP padrão, sem
            nenhum token de autenticação.
    """
    return prepare_header(username=None, password=None)


@pytest.fixture(scope="session", name="header_admin")
def fixture_header_admin(
    admin_credentials: dict,  # pylint: disable=unused-argument
) -> dict:
    """Authenticate in the API as an admin and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(
        username=admin_credentials["username"], password=admin_credentials["password"]
    )


@pytest.fixture(scope="session", name="header_usr_1")
def fixture_header_usr_1(
    register_user_1, user1_credentials: dict  # pylint: disable=unused-argument
) -> dict:
    """Authenticate in the API as user1 and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(
        username=user1_credentials["email"], password=user1_credentials["password"]
    )


@pytest.fixture(scope="session", name="header_usr_2")
def fixture_header_usr_2(
    register_user_2, user2_credentials: dict  # pylint: disable=unused-argument
) -> dict:
    """Authenticate in the API as user2 and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(
        username=user2_credentials["email"], password=user2_credentials["password"]
    )


@pytest.fixture(scope="function", name="input_pe")
def fixture_input_pe() -> dict:
    """Template de Plano de Entregas da Unidade.

    Returns:
        dict: template de exemplo
    """
    return json.load(open("data/plano_entregas.json", "r", encoding="utf-8"))


@pytest.fixture(scope="function", name="input_pt")
def fixture_input_pt() -> dict:
    """Template de Plano de Trabalho do Participante.

    Returns:
        dict: template de exemplo
    """
    return json.load(open("data/plano_trabalho.json", "r", encoding="utf-8"))


@pytest.fixture(scope="function", name="input_part")
def fixture_input_part() -> dict:
    """Template de Participante.

    Returns:
        dict: template de exemplo
    """
    return json.load(open("data/participante.json", "r", encoding="utf-8"))


@pytest.fixture(scope="session", name="client")
def fixture_client() -> Generator[httpx.Client, None, None]:
    """Cliente HTTP para ser usado nos testes.

    Returns:
        Generator[httpx.Client, None, None]: Uma instância de `httpx.Client`
        que pode ser usada para fazer requisições HTTP nos testes.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", name="admin_credentials")
def fixture_admin_credentials() -> dict:
    """Credenciais do usuário administrador da API.

    Returns:
        dict: Um dicionário contendo o nome de usuário (username) e a
            senha (password) do usuário administrador da API.
    """
    return {
        "username": API_PGD_ADMIN_USER,
        "password": API_PGD_ADMIN_PASSWORD,
    }


@pytest.fixture(scope="session", name="user1_credentials")
def fixture_user1_credentials() -> dict:
    """Credenciais do primeiro usuário de teste.

    Returns:
        dict: Um dicionário contendo as informações de credenciais do
            primeiro usuário de teste, incluindo nome de usuário, email,
            senha, status de administrador, etc.
    """
    return USERS_CREDENTIALS[0]


@pytest.fixture(scope="session", name="user2_credentials")
def fixture_user2_credentials() -> dict:
    """Credenciais do segundo usuário de teste.

    Returns:
        dict: Um dicionário contendo as informações de credenciais do
            segundo usuário de teste, incluindo nome de usuário, email,
            senha, status de administrador, etc.
    """
    return USERS_CREDENTIALS[1]


@pytest.fixture()
def example_pe(
    client: httpx.Client,
    input_pe: dict,
    header_usr_1: dict,
):
    """Cria um Plano de Entrega como exemplo."""
    client.put(
        f"/organizacao/SIAPE/{input_pe['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entregas']}",
        json=input_pe,
        headers=header_usr_1,
    )


@pytest.fixture()
def example_pe_unidade_3(
    client: httpx.Client,
    input_pe: dict,
    header_usr_1: dict,
):
    """Cria um Plano de Entrega como exemplo."""
    input_pe_3 = deepcopy(input_pe)
    input_pe_3["cod_unidade_autorizadora"] = 3
    client.put(
        f"/organizacao/SIAPE/{input_pe_3['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe_3['id_plano_entregas']}",
        json=input_pe_3,
        headers=header_usr_1,
    )


@pytest.fixture()
def example_pe_max_int(
    client: httpx.Client,
    input_pe: dict,
    header_usr_1: dict,
):
    """Cria um Plano de Entrega como exemplo usando o valor máximo
    permitido para cod_unidade_autorizadora."""
    new_input_pe = deepcopy(input_pe)
    new_input_pe["cod_unidade_autorizadora"] = MAX_INT
    client.put(
        f"/organizacao/SIAPE/{new_input_pe['cod_unidade_autorizadora']}"
        f"/plano_entregas/{new_input_pe['id_plano_entregas']}",
        json=new_input_pe,
        headers=header_usr_1,
    )


@pytest.fixture()
def example_pt(
    client: httpx.Client, input_pt: dict, user1_credentials: dict, header_usr_1: dict
):
    """Cria um Plano de Trabalho do Participante como exemplo."""
    client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )


@pytest.fixture()
def example_pt_unidade_3(
    client: httpx.Client,
    input_pt: dict,
    header_admin: dict,
):
    """Cria na unidade 3 um Plano de Trabalho do Participante como exemplo."""
    input_pt_3 = deepcopy(input_pt)
    input_pt_3["cod_unidade_autorizadora"] = 3
    client.put(
        f"/organizacao/{input_pt_3['origem_unidade']}"
        f"/{input_pt_3['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt_3['id_plano_trabalho']}",
        json=input_pt_3,
        headers=header_admin,
    )


@pytest.fixture()
def example_part(client: httpx.Client, input_part: dict, header_admin: dict):
    """Cria um exemplo de status de participante."""
    client.put(
        f"/organizacao/{input_part['origem_unidade']}"
        f"/{input_part['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        json=input_part,
        headers=header_admin,
    )


@pytest.fixture()
def example_part_autorizadora_2(client: httpx.Client, input_part: dict, header_admin: dict):
    """Cria um exemplo de status de participante com diferente SIAPE e lotação"""
    input_part_1 = deepcopy(input_part)
    input_part_1["cod_unidade_autorizadora"] = 2
    input_part_1["matricula_siape"] = "1234567"
    client.put(
        f"/organizacao/{input_part_1['origem_unidade']}"
        f"/{input_part_1['cod_unidade_autorizadora']}"
        f"/{input_part_1['cod_unidade_lotacao']}"
        f"/participante/{input_part_1['matricula_siape']}",
        json=input_part_1,
        headers=header_admin,
    )


@pytest.fixture()
def example_part_lotacao_99(client: httpx.Client, input_part: dict, header_admin: dict):
    """Cria um exemplo de status de participante com diferente SIAPE e lotação"""
    input_part_1 = deepcopy(input_part)
    input_part_1["cod_unidade_lotacao"] = 99
    input_part_1["matricula_siape"] = "1234567"
    client.put(
        f"/organizacao/{input_part_1['origem_unidade']}"
        f"/{input_part_1['cod_unidade_autorizadora']}"
        f"/{input_part_1['cod_unidade_lotacao']}"
        f"/participante/{input_part_1['matricula_siape']}",
        json=input_part_1,
        headers=header_admin,
    )


@pytest.fixture()
def example_part_max_int(client: httpx.Client, input_part: dict, header_admin: dict):
    """Cria exemplos de participantes com as combinações de códigos de
    unidade usando os inteiros máximos permitidos para os tipos de campo."""
    new_input_part = deepcopy(input_part)
    new_input_part["cod_unidade_lotacao"] = MAX_INT
    client.put(
        f"/organizacao/{new_input_part['origem_unidade']}"
        f"/{new_input_part['cod_unidade_autorizadora']}"
        f"/{new_input_part['cod_unidade_lotacao']}"
        f"/participante/{new_input_part['matricula_siape']}",
        json=new_input_part,
        headers=header_admin,
    )
    new_input_part["cod_unidade_lotacao"] = input_part["cod_unidade_lotacao"]
    new_input_part["cod_unidade_autorizadora"] = MAX_INT
    client.put(
        f"/organizacao/{new_input_part['origem_unidade']}"
        f"/{new_input_part['cod_unidade_autorizadora']}"
        f"/{new_input_part['cod_unidade_lotacao']}"
        f"/participante/{new_input_part['matricula_siape']}",
        json=new_input_part,
        headers=header_admin,
    )


@pytest.fixture()
def example_part_unidade_3(client: httpx.Client, input_part: dict, header_admin: dict):
    """Cria um exemplo de status de participante na unidade autorizadora 3."""
    input_part_1 = deepcopy(input_part)
    input_part_1["cod_unidade_autorizadora"] = 3
    client.put(
        f"/organizacao/{input_part_1['origem_unidade']}"
        f"/{input_part_1['cod_unidade_autorizadora']}"
        f"/{input_part_1['cod_unidade_lotacao']}"
        f"/participante/{input_part_1['matricula_siape']}",
        json=input_part_1,
        headers=header_admin,
    )


@pytest.fixture()
def truncate_pe():
    """Trunca a tabela de Planos de Entrega."""
    truncate_plano_entregas()


@pytest.fixture()
def truncate_pt():
    """Trunca a tabela de Planos de Trabalho."""
    truncate_plano_trabalho()


@pytest.fixture()
def truncate_participantes():
    """Trunca a tabela de Participantes."""
    truncate_participante()
