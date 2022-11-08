"""
Testes relacionados aos métodos de usuários.
"""
from requests import Session

from fastapi import status

from tests.conftest import register_user

def test_register_user_not_logged_in(
        truncate_users, client: Session, header_not_logged_in: dict):
    user_1 = register_user(client, "testx@api.com", "api", 0, header_not_logged_in)
    assert user_1.status_code == status.HTTP_401_UNAUTHORIZED

def test_register_user(truncate_users, client: Session, header_admin: dict):
    user_1 = register_user(client, "testx@api.com", "api", 0, header_admin)
    assert user_1.status_code == status.HTTP_201_CREATED

    user_2 = register_user(client, "testx@api.com", "api", 0, header_admin)
    assert user_2.status_code == status.HTTP_400_BAD_REQUEST
    assert user_2.json().get("detail", None) == "REGISTER_USER_ALREADY_EXISTS"

def test_authenticate(header_usr_1: dict):
    token = header_usr_1.get("Authorization")
    assert isinstance(token, str)
    assert "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9." in token

def test_get_user_self_not_logged_in(client: Session,
        header_not_logged_in: dict):
    response = client.get("/users/me", headers=header_not_logged_in)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_user_self_logged_in(client: Session, user1_credentials: dict,
        header_usr_1: dict):
    response = client.get("/users/me", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("email", None) == user1_credentials["username"]
    assert data.get("cod_unidade", None) == user1_credentials["cod_unidade"]
    assert data.get("is_active", None) == True

def test_patch_user_self_change_cod_unidade(client: Session,
        header_usr_1: dict):
    "Testa se o usuário pode alterar o seu próprio cod_unidade."
    response = client.patch(
        "/users/me",
        json={"cod_unidade": 3},
        headers=header_usr_1
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_forgot_password(client: Session, user1_credentials: dict):
    "Testa se o forgot password está operante."
    response = client.post(
        "/auth/forgot-password",
        json={"email": user1_credentials["username"]}
    )
    assert response.status_code == status.HTTP_202_ACCEPTED

def test_forgot_password_invalid_email(client: Session):
    "Testa se o forgot password está operante."
    response = client.post(
        "/auth/forgot-password",
        json={"email": "test.com"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reset_password_bad_token(client: Session):
    "Testa o reset password com um token inválido."
    response = client.post(
        "/auth/reset-password",
        json={"token":"foo", "password":"new-password"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

