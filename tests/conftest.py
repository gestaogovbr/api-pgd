"""
Funções auxiliares e fixtures dos testes.
"""
import os
import sys
import json
from typing import Generator, Optional

import httpx

from fastapi.testclient import TestClient
from httpx import Client
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from fief_admin import FiefAdminHelper
from api import app

# Fief admin helper object
fief_admin = FiefAdminHelper(
    api_token=os.environ.get("FIEF_MAIN_ADMIN_API_KEY"),
    base_url=os.environ.get("FIEF_BASE_TENANT_URL"),
)

USERS_CREDENTIALS = [
    {
        "username": "test1@api.com",
        "cod_SIAPE_instituidora": 1,
    },
    {
        "username": "test2@api.com",
        "cod_SIAPE_instituidora": 2,
    },
]


@pytest.fixture()
def input_pe() -> dict:
    """Template de Plano de Entregas da Unidade.

    Returns:
        dict: template de exemplo
    """
    return json.load(open("data/plano_entregas.json", "r", encoding="utf-8"))


@pytest.fixture()
def input_pt() -> dict:
    """Template de Plano de Trabalho do Participante.

    Returns:
        dict: template de exemplo
    """
    return json.load(open("data/plano_trabalho.json", "r", encoding="utf-8"))


@pytest.fixture()
def input_part() -> dict:
    """Template de Participante.

    Returns:
        dict: template de exemplo
    """
    return {
        "participante_ativo_inativo_pgd": 1,
        "matricula_siape": 123456,
        "cpf_participante": 99160773120,
        "modalidade_execucao": 3,
        "jornada_trabalho_semanal": 40,
    }


def prepare_header(username: Optional[str]) -> dict:
    """Prepara o cabeçalho para ser utilizado em requisições."""
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    if username:
        user_token = fief_admin.get_access_token_for_user(email=username)
        headers["Authorization"] = f"Bearer {user_token}"

    return headers


# Fixtures


@pytest.fixture(scope="module")
def client() -> Generator[Client, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_credentials() -> dict:
    return {
        "username": "admin@api.com",
        "cod_SIAPE_instituidora": 1,
    }


@pytest.fixture(scope="module")
def user1_credentials() -> dict:
    return USERS_CREDENTIALS[0]


@pytest.fixture(scope="module")
def user2_credentials() -> dict:
    return USERS_CREDENTIALS[1]


@pytest.fixture()
def example_pe(
    client: Client,
    input_pe: dict,
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
):
    """Cria um Plano de Entrega como exemplo."""
    client.put(
        f"/plano_entrega/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )


@pytest.fixture()
def example_pt(
    client: Client, input_pt: dict, user1_credentials: dict, header_usr_1: dict
):
    """Cria um Plano de Trabalho do Participante como exemplo."""
    client.put(
        f"/plano_trabalho/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/{input_pt['id_plano_trabalho_participante']}",
        json=input_pt,
        headers=header_usr_1,
    )


@pytest.fixture()
def example_part(client: Client, input_part: dict, header_usr_1: dict):
    client.put("/participante/123456", json=input_part, headers=header_usr_1)


@pytest.fixture()
def truncate_pe(client: Client, header_admin: dict):
    client.post("/truncate_plano_entregas", headers=header_admin)


@pytest.fixture()
def truncate_pt(client: Client, header_admin: dict):
    client.post("/truncate_plano_trabalho", headers=header_admin)


@pytest.fixture()
def truncate_participantes(client: Client, header_admin: dict):
    client.post("/truncate_participantes", headers=header_admin)


@pytest.fixture(scope="module")
def truncate_users():
    for user in USERS_CREDENTIALS:
        user_search = fief_admin.search_user(email=user["username"]).json()
        if user_search["count"] > 0:
            fief_admin.delete_user(email=user["username"])


@pytest.fixture(scope="module")
def register_admin(
    truncate_users,
    admin_credentials: dict,
) -> httpx.Response:
    return fief_admin.register_user(
        email=admin_credentials["username"],
        cod_SIAPE_instituidora=admin_credentials["cod_SIAPE_instituidora"],
    )


@pytest.fixture(scope="module")
def register_user_1(
    truncate_users,
    user1_credentials: dict,
) -> httpx.Response:
    return fief_admin.register_user(
        email=user1_credentials["username"],
        cod_SIAPE_instituidora=user1_credentials["cod_SIAPE_instituidora"],
    )


@pytest.fixture(scope="module")
def register_user_2(
    truncate_users,
    user2_credentials: dict,
) -> httpx.Response:
    return fief_admin.register_user(
        email=user2_credentials["username"],
        cod_SIAPE_instituidora=user2_credentials["cod_SIAPE_instituidora"],
    )


@pytest.fixture(scope="module")
def header_not_logged_in() -> dict:
    return prepare_header(username=None)


@pytest.fixture(scope="module")
def header_admin(register_admin, admin_credentials: dict) -> dict:
    """Authenticate in the API as an admin and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(username=admin_credentials["username"])


@pytest.fixture(scope="module")
def header_usr_1(register_user_1, user1_credentials: dict) -> dict:
    """Authenticate in the API as user1 and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(username=user1_credentials["username"])


@pytest.fixture(scope="module")
def header_usr_2(register_user_2, user2_credentials: dict) -> dict:
    """Authenticate in the API as user2 and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(username=user2_credentials["username"])
