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
from crud import (
    truncate_plano_entregas,
    truncate_plano_trabalho,
    truncate_status_participante,
)
from db_config import get_db
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


@pytest.fixture(scope="module", name="input_pe")
def fixture_input_pe() -> dict:
    """Template de Plano de Entregas da Unidade.

    Returns:
        dict: template de exemplo
    """
    return json.load(open("data/plano_entregas.json", "r", encoding="utf-8"))


@pytest.fixture(scope="module", name="input_pt")
def fixture_input_pt() -> dict:
    """Template de Plano de Trabalho do Participante.

    Returns:
        dict: template de exemplo
    """
    return json.load(open("data/plano_trabalho.json", "r", encoding="utf-8"))


@pytest.fixture(scope="module", name="input_part")
def fixture_input_part() -> dict:
    """Template de Participante.

    Returns:
        dict: template de exemplo
    """
    return {
        "participante_ativo_inativo_pgd": 1,
        "matricula_siape": "123456",
        "cpf_participante": "64635210600",
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


@pytest.fixture(scope="module", name="client")
def fixture_client() -> Generator[Client, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module", name="admin_credentials")
def fixture_admin_credentials() -> dict:
    return {
        "username": "admin@api.com",
        "cod_SIAPE_instituidora": 1,
    }


@pytest.fixture(scope="module", name="user1_credentials")
def fixture_user1_credentials() -> dict:
    return USERS_CREDENTIALS[0]


@pytest.fixture(scope="module", name="user2_credentials")
def fixture_user2_credentials() -> dict:
    return USERS_CREDENTIALS[1]


@pytest.fixture()
def example_pe(
    client: Client,
    input_pe: dict,
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
def example_part(
    client: Client, input_part: dict, user1_credentials: dict, header_usr_1: dict
):
    client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/participante/{input_part['cpf_participante']}",
        json=input_part,
        headers=header_usr_1,
    )


@pytest.fixture()
def truncate_pe():
    db = get_db()
    truncate_plano_entregas(db)


@pytest.fixture()
def truncate_pt():
    db = get_db()
    truncate_plano_trabalho(db)


@pytest.fixture()
def truncate_participantes():
    db = get_db()
    truncate_status_participante(db)


@pytest.fixture(scope="module", name="truncate_users")
def fixture_truncate_users(admin_credentials: dict):
    for user in USERS_CREDENTIALS + [admin_credentials]:
        user_search = fief_admin.search_user(email=user["username"]).json()
        if user_search["count"] > 0:
            response = fief_admin.delete_user(email=user["username"])
            response.raise_for_status()


@pytest.fixture(scope="module", name="register_admin")
def fixture_register_admin(
    truncate_users,  # pylint: disable=unused-argument
    admin_credentials: dict,
) -> httpx.Response:
    response = fief_admin.register_user(
        email=admin_credentials["username"],
        cod_SIAPE_instituidora=admin_credentials["cod_SIAPE_instituidora"],
    )
    response.raise_for_status()
    return response


@pytest.fixture(scope="module", name="register_user_1")
def fixture_register_user_1(
    truncate_users,  # pylint: disable=unused-argument
    user1_credentials: dict,
) -> httpx.Response:
    response = fief_admin.register_user(
        email=user1_credentials["username"],
        cod_SIAPE_instituidora=user1_credentials["cod_SIAPE_instituidora"],
    )
    response.raise_for_status()
    return response


@pytest.fixture(scope="module", name="register_user_2")
def fixture_register_user_2(
    truncate_users,  # pylint: disable=unused-argument
    user2_credentials: dict,
) -> httpx.Response:
    response = fief_admin.register_user(
        email=user2_credentials["username"],
        cod_SIAPE_instituidora=user2_credentials["cod_SIAPE_instituidora"],
    )
    response.raise_for_status()
    return response


@pytest.fixture(scope="module")
def header_not_logged_in() -> dict:
    return prepare_header(username=None)


@pytest.fixture(scope="module", name="header_admin")
def fixture_header_admin(
    register_admin, admin_credentials: dict  # pylint: disable=unused-argument
) -> dict:
    """Authenticate in the API as an admin and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(username=admin_credentials["username"])


@pytest.fixture(scope="module", name="header_usr_1")
def fixture_header_usr_1(
    register_user_1, user1_credentials: dict  # pylint: disable=unused-argument
) -> dict:
    """Authenticate in the API as user1 and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(username=user1_credentials["username"])


@pytest.fixture(scope="module", name="header_usr_2")
def fixture_header_usr_2(
    register_user_2, user2_credentials: dict  # pylint: disable=unused-argument
) -> dict:
    """Authenticate in the API as user2 and return a dict with bearer
    header parameter to be passed to API's requests."""
    return prepare_header(username=user2_credentials["username"])
