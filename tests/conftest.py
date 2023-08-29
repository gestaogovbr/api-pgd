"""
Funções auxiliares e fixtures dos testes.
"""
import os
import sys
import subprocess
import json
from typing import Generator, Optional

import httpx

from fastapi.testclient import TestClient
from httpx import Client
from fastapi import status
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from fief_admin import FiefAdminHelper
from api import app

# Fief admin helper object
fief_admin = FiefAdminHelper(
    api_token=os.environ.get("FIEF_MAIN_ADMIN_API_KEY"),
    base_url=os.environ.get("FIEF_BASE_TENANT_URL"),
)


def prepare_header(username: Optional[str], password: Optional[str]) -> dict:
    """Prepara o cabeçalho para ser utilizado em requisições."""
    # TODO: Refatorar e resolver utilizando o objeto TestClient
    token_user = None

    if username and password:
        # usuário especificado, é necessário fazer login
        url = "http://localhost:5057/auth/jwt/login"

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        payload = "&".join(
            [
                "accept=application%2Fjson",
                "Content-Type=application%2Fjson",
                f"username={username}",
                f"password={password}",
            ]
        )

        response = httpx.request("POST", url, headers=headers, data=payload)
        response_dict = json.loads(response.text)
        token_user = response_dict.get("access_token")
        print(token_user)

    headers = {"accept": "application/json", "Content-Type": "application/json"}
    if token_user:
        headers["Authorization"] = f"Bearer {token_user}"

    return headers


# Fixtures


@pytest.fixture(scope="module")
def client() -> Generator[Client, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_credentials() -> dict:
    return {"username": "admin@api.com", "password": "1234", "cod_unidade": 1}


@pytest.fixture(scope="module")
def user1_credentials() -> dict:
    return {"username": "test1@api.com", "password": "api", "cod_unidade": 1}


@pytest.fixture(scope="module")
def user2_credentials() -> dict:
    return {"username": "test2@api.com", "password": "api", "cod_unidade": 2}


@pytest.fixture()
def example_pe(client: Client, input_pt: dict, header_usr_1: dict):
    client.put("/plano_entrega/555", json=input_pt, headers=header_usr_1)


@pytest.fixture()
def example_part(client: Client, input_part: dict, header_usr_1: dict):
    client.put("/participante/123456", json=input_part, headers=header_usr_1)


@pytest.fixture()
def truncate_pt(client: Client, header_admin: dict):
    client.post("/truncate_pts_atividades", headers=header_admin)


@pytest.fixture()
def truncate_part(client: Client, header_admin: dict):
    client.post("/truncate_participantes", headers=header_admin)


@pytest.fixture(scope="module")
def truncate_users():
    p = subprocess.Popen(
        ["/usr/local/bin/python", "/home/api-pgd/admin_tool.py", "--truncate-users"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


@pytest.fixture(scope="module")
def register_admin(truncate_users, admin_credentials: dict):
    email = admin_credentials["username"]
    cod_unidade = admin_credentials["cod_unidade"]
    password = admin_credentials["password"]
    p = subprocess.Popen(
        [
            "/usr/local/bin/python",
            "/home/api-pgd/admin_tool.py",
            "--create_superuser",
            "--show_password",
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    p.communicate(input="\n".join([email, str(cod_unidade), password, password]))[0]


@pytest.fixture(scope="module")
def register_user_1(
    client: Client,
    truncate_users,
    register_admin,
    header_admin: dict,
    user1_credentials: dict,
) -> httpx.Response:
    return fief_admin.register_user(
        email=user1_credentials["username"],
        password=user1_credentials["password"],
        cod_unidade=user1_credentials["cod_unidade"],
    )


@pytest.fixture(scope="module")
def register_user_2(
    client: Client,
    truncate_users,
    register_admin,
    header_admin: dict,
    user2_credentials: dict,
) -> httpx.Response:
    return fief_admin.register_user(
        email=user2_credentials["username"],
        password=user2_credentials["password"],
        cod_unidade=user2_credentials["cod_unidade"],
    )


@pytest.fixture(scope="module")
def header_not_logged_in() -> dict:
    return prepare_header(username=None, password=None)


@pytest.fixture(scope="module")
def header_admin(register_admin, admin_credentials: dict) -> dict:
    return prepare_header(
        username=admin_credentials["username"], password=admin_credentials["password"]
    )


@pytest.fixture(scope="module")
def header_usr_1(register_user_1, user1_credentials: dict) -> dict:
    """Authenticate in the API as user1 and return a dict with bearer
    header parameter to be passed to apis requests."""
    return prepare_header(
        username=user1_credentials["username"], password=user1_credentials["password"]
    )


@pytest.fixture(scope="module")
def header_usr_2(register_user_2, user2_credentials: dict) -> dict:
    """Authenticate in the API as user2 and return a dict with bearer
    header parameter to be passed to apis requests."""
    return prepare_header(
        username=user2_credentials["username"], password=user2_credentials["password"]
    )
