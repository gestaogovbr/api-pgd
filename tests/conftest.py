"""
Funções auxiliares e fixtures dos testes.
"""
import os
import subprocess
import json
import urllib
from typing import Generator, Optional
from functools import cached_property

import httpx

from fastapi.testclient import TestClient
from httpx import Client
from fastapi import status
import pytest

# from api import app

# Helper functions


class FiefAdminHelper:
    """
    A helper class for interacting with the Fief API using admin authentication.

    Args:
        api_token (str): The API token for admin authentication.
        base_url (str): The base URL for the Fief API.

    Methods:
        fief_admin_call(method, local_url, params=None, data=None):
            Calls the Fief API with an admin token.
        get_fief_tenant():
            Get the tenant id for the first tenant registered in Fief.
        get_fief_client():
            Get the client id for the first client registered in Fief.
        register_user(email, password, cod_unidade):
            Registers a new user in Fief.
    """

    def __init__(self, api_token: str, base_url: str):
        """
        Initialize the Fief_Admin_Helper class.
        """
        self.api_token = api_token
        self.base_url = base_url

    def fief_admin_call(
        self, method: str, local_url: str, params: dict = None, data: dict = None
    ) -> httpx.Response:
        """
        Calls the Fief API with an admin token.

        Args:
            method (str): HTTP method to use.
            local_url (str): The local part of the URL.
            params (dict, optional): Parameters for the URL. Defaults to None.
            data (dict, optional): Dictionary to post. Defaults to None.

        Returns:
            httpx.Response: The Response object returned by httpx.
        """
        url = f"{self.base_url}/admin/api/{local_url}"
        if params:
            url += f"?{urllib.parse.urlencode(params)}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_token}",
        }

        if method in ["POST", "PUT"]:
            headers["content-type"] = "application/json"
            return httpx.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
            )
        return httpx.request(
            method=method,
            url=url,
            headers=headers,
        )

    @cached_property
    def first_tenant(self) -> str:
        """
        Get the tenant id for the first tenant registered in Fief.

        Returns:
            str: The tenant id.
        """
        return self.fief_admin_call(
            method="GET",
            local_url="tenants/",
            params={"limit": 1, "skip": 0},
        ).json()["results"][0]["id"]

    @cached_property
    def first_client(self) -> str:
        """
        Get the client id for the first client registered in Fief.

        Returns:
            str: The client id.
        """
        return self.fief_admin_call(
            method="GET",
            local_url="clients/",
            params={"tenant": self.first_tenant},
        ).json()["results"][0]["id"]

    def register_user(
        self, email: str, password: str, cod_unidade: int
    ) -> httpx.Response:
        """
        Registers a new user in Fief.

        Args:
            email (str): User's email.
            password (str): User's password.
            cod_unidade (int): User's organizational unit code.

        Returns:
            httpx.Response: The Response object returned by httpx.
        """
        fields = {"cod_unidade": cod_unidade}
        data = {
            "email": email,
            "password": password,
            "is_active": True,
            "is_superuser": False,
            "is_verified": False,
            "fields": fields,
            "tenant_id": self.first_tenant,
        }
        return self.fief_admin_call(
            method="POST",
            local_url="users/",
            data=data,
        )


# Exemplo de uso da classe
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


@pytest.fixture()
def input_pt() -> dict:
    pt_json = {
        "cod_plano": "555",
        "situacao": "string",
        "matricula_siape": 0,
        "cpf": "99160773120",
        "nome_participante": "string",
        "cod_unidade_exercicio": 0,
        "nome_unidade_exercicio": "string",
        "modalidade_execucao": 1,
        "carga_horaria_semanal": 10,
        "data_inicio": "2021-01-07",
        "data_fim": "2021-01-12",
        "carga_horaria_total": 0.0,
        "data_interrupcao": "2021-01-07",
        "entregue_no_prazo": True,
        "horas_homologadas": 1.5,
        "atividades": [
            {
                "id_atividade": "2",
                "nome_grupo_atividade": "string",
                "nome_atividade": "string",
                "faixa_complexidade": "string",
                "parametros_complexidade": "string",
                "tempo_presencial_estimado": 0.0,
                "tempo_presencial_programado": 0.0,
                "tempo_presencial_executado": None,
                "tempo_teletrabalho_estimado": 0.0,
                "tempo_teletrabalho_programado": 0.0,
                "tempo_teletrabalho_executado": None,
                "entrega_esperada": "string",
                "qtde_entregas": 0,
                "qtde_entregas_efetivas": 0,
                "avaliacao": 0,
                "data_avaliacao": "2021-01-15",
                "justificativa": "string",
            },
            {
                "id_atividade": "3",
                "nome_grupo_atividade": "string",
                "nome_atividade": "string",
                "faixa_complexidade": "string",
                "parametros_complexidade": "string",
                "tempo_presencial_estimado": 0.0,
                "tempo_presencial_programado": 0.0,
                "tempo_presencial_executado": None,
                "tempo_teletrabalho_estimado": 0.0,
                "tempo_teletrabalho_programado": 0.0,
                "tempo_teletrabalho_executado": None,
                "entrega_esperada": "string",
                "qtde_entregas": 0,
                "qtde_entregas_efetivas": 0,
                "avaliacao": 0,
                "data_avaliacao": "2021-01-15",
                "justificativa": "string",
            },
        ],
    }
    return pt_json


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
def example_pt(client: Client, input_pt: dict, header_usr_1: dict):
    client.put(f"/plano_trabalho/555", json=input_pt, headers=header_usr_1)


@pytest.fixture()
def truncate_pt(client: Client, header_admin: dict):
    client.post(f"/truncate_pts_atividades", headers=header_admin)


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
        user1_credentials["username"],
        user1_credentials["password"],
        user1_credentials["cod_unidade"],
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
        user2_credentials["username"],
        user2_credentials["password"],
        user2_credentials["cod_unidade"],
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
