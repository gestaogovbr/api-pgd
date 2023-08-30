"""
Testes relacionados aos métodos de usuários.
"""
from httpx import Client

from fastapi import status

from tests.conftest import fief_admin

def test_authenticate(header_usr_1: dict):
    token = header_usr_1.get("Authorization")
    assert isinstance(token, str)
    assert "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9." in token

def test_get_user_self_not_logged_in(client: Client,
        header_not_logged_in: dict):
    response = client.get("/users/me", headers=header_not_logged_in)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_user_self_logged_in(client: Client, user1_credentials: dict,
        header_usr_1: dict):
    response = client.get("/users/me", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("email", None) == user1_credentials["username"]
    assert data.get("cod_unidade", None) == user1_credentials["cod_unidade"]
    assert data.get("is_active", None) == True

def test_patch_user_self_change_cod_unidade(client: Client,
        header_usr_1: dict):
    "Testa se o usuário pode alterar o seu próprio cod_unidade."
    response = client.patch(
        "/users/me",
        json={"cod_unidade": 3},
        headers=header_usr_1
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_forgot_password(client: Client, user1_credentials: dict):
    "Testa se o forgot password está operante."
    response = client.post(
        "/auth/forgot-password",
        json={"email": user1_credentials["username"]}
    )
    assert response.status_code == status.HTTP_202_ACCEPTED

def test_forgot_password_invalid_email(client: Client):
    "Testa se o forgot password está operante."
    response = client.post(
        "/auth/forgot-password",
        json={"email": "test.com"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reset_password_bad_token(client: Client):
    "Testa o reset password com um token inválido."
    response = client.post(
        "/auth/reset-password",
        json={"token":"foo", "password":"new-password"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

