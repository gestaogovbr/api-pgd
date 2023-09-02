"""
Testes relacionados aos métodos de usuários.
"""
from httpx import Client

from fastapi import status

from tests.conftest import fief_admin


def test_authenticate(header_usr_1: dict):
    token = header_usr_1.get("Authorization")
    assert isinstance(token, str)


def test_get_user_self_not_logged_in(client: Client, header_not_logged_in: dict):
    response = client.get("/user", headers=header_not_logged_in)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_self_logged_in(
    client: Client, user1_credentials: dict, header_usr_1: dict
):
    response = client.get("/user", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("email", None) == user1_credentials["username"]
    user_fields = data.get("fields", None)
    assert isinstance(user_fields, dict)
    assert (
        user_fields.get("cod_SIAPE_instituidora", None)
        == user1_credentials["cod_SIAPE_instituidora"]
    )
    assert data.get("is_active", None) == True
