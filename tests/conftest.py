"""
Funções auxiliares e fixtures dos testes.
"""
import os
import subprocess
import json
from typing import Generator, Optional

import httpx

from fastapi.testclient import TestClient
from httpx import Client
from fastapi import status
from api import app

import pytest

# Helper functions

def fief_admin_call(method: str, local_url: str, data: dict = None) -> httpx.Response:
    """Calls the Fief API with an admin token.

    Args:
        method (str): http method to use
        local_url (str): the local part of the url
        data, (dict, optional): dictionary to post. Defaults to None.

    Returns:
        httpx.Response: the Response object returned by httpx.
    """
    api_token = os.environ("FIEF_MAIN_ADMIN_API_KEY")
    base_url = os.environ("FIEF_BASE_TENANT_URL")
    if method in ["POST", "PUT"]:
        return httpx.request(
        method=method,
        url=f"{base_url}/admin/api/{local_url}",
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer: {api_token}",
        },
        data=data,
    )
    return httpx.request(
        method=method,
        url=f"{base_url}/admin/api/{local_url}",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer: {api_token}",
        },
    )

def register_user(
        email: str,
        password: str,
        cod_unidade: int,
    ) -> httpx.Response:
    """Registers a new user in Fief.

    Args:
        email (str): user's email.
        password (str): user's password.
        cod_unidade (int): user's organizational unit code.

    Returns:
        httpx.Response: the Response object returned by httpx.
    """
    tenant_id = fief_admin_call(
        method="GET",
        local_url="tenants/?limit=10&skip=0",
    ).json()["results"][0]["id"]

    fields = {"cod_unidade": cod_unidade}

    data = {
            "email": email,
            "password": password,
            "is_active": True,
            "is_superuser": False,
            "is_verified": False,
            "fields": fields,
            "tenant_id": tenant_id,
    }

    return fief_admin_call(
        method="POST",
        local_url="users/",
        data=data,
    )

def prepare_header(username: Optional[str], password: Optional[str]) -> dict:
    """Prepara o cabeçalho para ser utilizado em requisições.
    """
    #TODO: Refatorar e resolver utilizando o objeto TestClient
    token_user = None

    if username and password:
        # usuário especificado, é necessário fazer login
        url = "http://localhost:5057/auth/jwt/login"

        headers = {
        "Content-Type": "application/x-www-form-urlencoded"
        }

        payload="&".join([
            "accept=application%2Fjson",
            "Content-Type=application%2Fjson",
            f"username={username}",
            f"password={password}"
        ])

        response = httpx.request("POST", url, headers=headers, data=payload)
        response_dict = json.loads(response.text)
        token_user = response_dict.get("access_token")
        print(token_user)

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
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
                "justificativa": "string"
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
                "justificativa": "string"
            }
        ]
    }
    return pt_json


@pytest.fixture(scope="module")
def admin_credentials() -> dict:
    return {
        "username": "admin@api.com",
        "password": "1234",
        "cod_unidade": 1
    }

@pytest.fixture(scope="module")
def user1_credentials() -> dict:
    return {
        "username": "test1@api.com",
        "password": "api",
        "cod_unidade": 1
    }

@pytest.fixture(scope="module")
def user2_credentials() -> dict:
    return {
        "username": "test2@api.com",
        "password": "api",
        "cod_unidade": 2
    }

@pytest.fixture()
def example_pt(client: Client, input_pt: dict, header_usr_1: dict):
    client.put(f"/plano_trabalho/555",
                          json=input_pt,
                          headers=header_usr_1)

@pytest.fixture()
def truncate_pt(client: Client, header_admin: dict):
    client.post(f"/truncate_pts_atividades", headers=header_admin)

@pytest.fixture(scope="module")
def truncate_users():
    p = subprocess.Popen(
        [
            "/usr/local/bin/python",
            "/home/api-pgd/admin_tool.py",
            "--truncate-users"
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
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
            "--show_password"
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    p.communicate(input="\n".join([
        email, str(cod_unidade), password, password
    ]))[0]

@pytest.fixture(scope="module")
def register_user_1(
    client: Client,
    truncate_users,
    register_admin,
    header_admin: dict,
    user1_credentials: dict
    ) -> httpx.Response:
    return register_user(user1_credentials["username"],
        user1_credentials["password"], user1_credentials["cod_unidade"])

@pytest.fixture(scope="module")
def register_user_2(
    client: Client,
    truncate_users,
    register_admin,
    header_admin: dict,
    user2_credentials: dict
    ) -> httpx.Response:
    return register_user(user2_credentials["username"],
        user2_credentials["password"], user2_credentials["cod_unidade"])

@pytest.fixture(scope="module")
def header_not_logged_in() -> dict:
    return prepare_header(username=None, password=None)

@pytest.fixture(scope="module")
def header_admin(register_admin, admin_credentials: dict) -> dict:
    return prepare_header(
        username=admin_credentials["username"],
        password=admin_credentials["password"])

@pytest.fixture(scope="module")
def header_usr_1(register_user_1, user1_credentials: dict) -> dict:
    """Authenticate in the API as user1 and return a dict with bearer
    header parameter to be passed to apis requests."""
    return prepare_header(
        username=user1_credentials["username"],
        password=user1_credentials["password"])

@pytest.fixture(scope="module")
def header_usr_2(register_user_2, user2_credentials: dict) -> dict:
    """Authenticate in the API as user2 and return a dict with bearer
    header parameter to be passed to apis requests."""
    return prepare_header(
        username=user2_credentials["username"],
        password=user2_credentials["password"])
