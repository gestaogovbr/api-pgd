"""
Funções auxiliares e fixtures dos testes.
"""
import subprocess
import json
from typing import Generator, Optional

from requests.models import Response as HTTPResponse
import requests

from fastapi.testclient import TestClient
from requests import Session
from fastapi import status
from api import app

import pytest

# Helper functions

def register_user(
        client: Session,
        email: str,
        password: str,
        cod_unidade: int,
        headers: dict
    ) -> HTTPResponse:
    data = {
        "email": email,
        "password": password,
        "cod_unidade": cod_unidade,
    }
    return client.post(
        f"/auth/register",
        json=data,
        headers=headers
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

        response = requests.request("POST", url, headers=headers, data=payload)
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
def client() -> Generator[Session, None, None]:
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
        "horas_homologadas": 0.0,
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
def example_pt(client: Session, input_pt: dict, header_usr_1: dict):
    client.put(f"/plano_trabalho/555",
                          json=input_pt,
                          headers=header_usr_1)

@pytest.fixture()
def truncate_pt(client: Session, header_admin: dict):
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
    client: Session,
    truncate_users,
    register_admin,
    header_admin: dict,
    user1_credentials: dict
    ) -> HTTPResponse:
    return register_user(client, user1_credentials["username"],
        user1_credentials["password"], user1_credentials["cod_unidade"],
        header_admin)

@pytest.fixture(scope="module")
def register_user_2(
    client: Session,
    truncate_users,
    register_admin,
    header_admin: dict,
    user2_credentials: dict
    ) -> HTTPResponse:
    return register_user(client, user2_credentials["username"],
        user2_credentials["password"], user2_credentials["cod_unidade"],
        header_admin)

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


