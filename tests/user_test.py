"""
Testes relacionados aos métodos de autenticação e usuários.

Disclaimer:
    * header_usr_1: dict is_admin=True
    * header_usr_2: dict is_admin=True
"""

from httpx import Client
from fastapi import status


USERS_TEST = [
    # to create and delete
    {
        "email": "user_test_0@api.com",
        "password": "secret",
        "is_admin": False,
        "disabled": False,
        "cod_SIAPE_instituidora": 1,
    },
    # to get and delete (not created)
    {
        "email": "user_test_1@api.com",
        "password": "secret",
        "is_admin": False,
        "disabled": False,
        "cod_SIAPE_instituidora": 1,
    },
    # to get without one of required fields (email, password, cod_SIAPE_instituidora)
    {
        "email": "user_test_2@api.com",
        "password": "secret",
        # "cod_SIAPE_instituidora": 1,
    },
    # to create with bad email format. mind that is_admin and disabled are optionals
    {
        "email": "not_a_email",
        "password": "secret",
        # "is_admin": False, # defaults do False
        # "disabled": False, # defaults do False
        "cod_SIAPE_instituidora": 1,
    },
]


# post /token
def test_authenticate(header_usr_1: dict):
    token = header_usr_1.get("Authorization")
    assert isinstance(token, str)


# get /users
def test_get_all_users_not_logged_in(client: Client, header_not_logged_in: dict):
    response = client.get("/users", headers=header_not_logged_in)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_all_users_logged_in_not_admin(client: Client, header_usr_2: dict):
    response = client.get("/users", headers=header_usr_2)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_all_users_logged_in_admin(client: Client, header_usr_1: dict):
    response = client.get("/users", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK

# get /user
def test_get_user_not_logged_in(client: Client, header_not_logged_in: dict):
    response = client.get("/user/foo@oi.com", headers=header_not_logged_in)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_logged_in_not_admin(
    client: Client, user2_credentials: dict, header_usr_2: dict # user is_admin=False
):
    response = client.get(f"/user/{user2_credentials['email']}", headers=header_usr_2)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_as_admin(
    client: Client,
    user1_credentials: dict,
    header_usr_1: dict # user is_admin=True
):
    response = client.get(f"/user/{user1_credentials['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK


def test_get_user_not_exists(
    client: Client, header_usr_1: dict # user is_admin=True
):
    response = client.get(f"/user/{USERS_TEST[1]['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_self_logged_in(
    client: Client,
    user1_credentials: dict,
    header_usr_1: dict # user is_admin=True
):
    response = client.get(f"/user/{user1_credentials['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("email", None) == user1_credentials["email"]
    assert data.get("is_admin", None) == user1_credentials["is_admin"]
    print("###############")
    print(data)
    assert data.get("disabled", None) == user1_credentials["disabled"]
    assert (
        data.get("cod_SIAPE_instituidora", None)
        == user1_credentials["cod_SIAPE_instituidora"]
    )


# create /user
def test_create_user_not_logged_in(client: Client, header_not_logged_in: dict):
    response = client.put(
        f"/user/{USERS_TEST[0]['email']}", headers=header_not_logged_in, json=USERS_TEST[0]
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_user_logged_in_not_admin(
        client: Client,
        header_usr_2: dict # user is_admin=False
    ):
    response = client.put(
        f"/user/{USERS_TEST[0]['email']}", headers=header_usr_2, json=USERS_TEST[0]
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_user_logged_in_admin(
        client: Client,
        header_usr_1: dict # user is_admin=True
    ):
    response = client.put(
        f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1, json=USERS_TEST[0]
    )
    assert response.status_code == status.HTTP_200_OK


def test_create_user_without_required_fields(
        client: Client,
        header_usr_1: dict # user is_admin=True
    ):
    response = client.put(
        f"/user/{USERS_TEST[2]['email']}", headers=header_usr_1, json=USERS_TEST[2]
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_bad_email_format(
    client: Client,
    header_usr_1: dict # user is_admin=True
):
    response = client.put(
        f"/user/{USERS_TEST[3]['email']}", headers=header_usr_1, json=USERS_TEST[3]
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# update /user
def test_update_user(
        client: Client,
        header_usr_1: dict # user is_admin=True
    ):
    # get
    r_1 = client.get(f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1)
    data_before = r_1.json()

    # update
    new_data = data_before
    new_data["cod_SIAPE_instituidora"] = 99
    new_data["password"] = "new_secret"
    r_2 = client.put(
        f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1, json=new_data
    )
    assert r_2.status_code == status.HTTP_200_OK

    # get new value
    r_3 = client.get(f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1)
    data_after = r_3.json()

    assert data_before.get("cod_SIAPE_instituidora", None) == data_after.get("cod_SIAPE_instituidora", None)


# delete /user
def test_delete_user_not_logged_in(client: Client, header_not_logged_in: dict):
    response = client.delete(
        f"/user/{USERS_TEST[0]['email']}", headers=header_not_logged_in)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_user_logged_in_not_admin(
        client: Client,
        header_usr_2: dict # user is_admin=False
    ):
    response = client.delete(
        f"/user/{USERS_TEST[0]['email']}", headers=header_usr_2)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_user_logged_in_admin(
        client: Client,
        header_usr_1: dict # user is_admin=True
    ):
    response = client.delete(
        f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK


def test_delete_user_not_exists_logged_in_admin(
        client: Client,
        header_usr_1: dict # user is_admin=True
    ):
    response = client.delete(
        f"/user/{USERS_TEST[1]['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_yourself(client: Client, user1_credentials: dict, header_usr_1: dict):
    response = client.delete(
        f"/user/{user1_credentials['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED