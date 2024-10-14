"""
Testes relacionados aos métodos de autenticação e usuários.

Disclaimer:
    * header_usr_1: dict is_admin=True
    * header_usr_2: dict is_admin=True
"""

from datetime import datetime
from imaplib import IMAP4
import email
import re
from typing import Generator

from httpx import Client, HTTPStatusError
from fastapi import status
import pytest

from .conftest import get_bearer_token


USERS_TEST = [
    # to create and delete
    {
        "email": "user_test_0@api.com",
        "password": "secret",
        "is_admin": False,
        "disabled": False,
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 1,
        "sistema_gerador": "API PGD CI Test",
    },
    # to get and delete (not created)
    {
        "email": "user_test_1@api.com",
        "password": "secret",
        "is_admin": False,
        "disabled": False,
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 1,
        "sistema_gerador": "API PGD CI Test",
    },
    # to get without one of required fields (email, password, cod_unidade_autorizadora)
    {
        "email": "user_test_2@api.com",
        "password": "secret",
        # "cod_unidade_autorizadora": 1,
    },
    # to create with bad email format. mind that is_admin and disabled are optionals
    {
        "email": "not_a_email",
        "password": "secret",
        # "is_admin": False, # defaults do False
        # "disabled": False, # defaults do False
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 1,
        "sistema_gerador": "API PGD CI Test",
    },
]

TOKEN_IN_MESSAGE = re.compile(r"<code>([^<]+)</code>")


# post /token
def test_authenticate(header_usr_1: dict):
    token = header_usr_1.get("Authorization")
    assert isinstance(token, str)


def test_attempt_log_in_disabled_user(
    truncate_users,  # pylint: disable=unused-argument
    register_user_1: dict,  # pylint: disable=unused-argument
    header_admin: dict,  # pylint: disable=unused-argument
    client: Client,
    user1_credentials: dict,
):
    """Cria um novo usuário, o desabilita e tenta logar com esse usuário."""
    user1_data = user1_credentials.copy()

    # update user 1 and disable it
    user1_data["disabled"] = True
    response = client.put(
        f"/user/{user1_data['email']}",
        headers=header_admin,
        json=user1_data,
    )
    assert response.status_code == status.HTTP_200_OK

    # try to log in as user 1
    with pytest.raises(HTTPStatusError):
        get_bearer_token(username=user1_data["email"], password=user1_data["password"])


# get /users
def test_get_all_users_not_logged_in(client: Client, header_not_logged_in: dict):
    response = client.get("/users", headers=header_not_logged_in)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_all_users_logged_in_not_admin(client: Client, header_usr_2: dict):
    response = client.get("/users", headers=header_usr_2)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_all_users_logged_in_admin(client: Client, header_usr_1: dict):
    response = client.get("/users", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK


# get /user
def test_get_user_not_logged_in(client: Client, header_not_logged_in: dict):
    response = client.get("/user/foo@oi.com", headers=header_not_logged_in)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_logged_in_not_admin(
    client: Client, user2_credentials: dict, header_usr_2: dict  # user is_admin=False
):
    response = client.get(f"/user/{user2_credentials['email']}", headers=header_usr_2)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_user_as_admin(
    client: Client, user1_credentials: dict, header_usr_1: dict  # user is_admin=True
):
    response = client.get(f"/user/{user1_credentials['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK


def test_get_user_not_exists(client: Client, header_usr_1: dict):  # user is_admin=True
    response = client.get(f"/user/{USERS_TEST[1]['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_self_logged_in(
    client: Client, user1_credentials: dict, header_usr_1: dict  # user is_admin=True
):
    response = client.get(f"/user/{user1_credentials['email']}", headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("email", None) == user1_credentials["email"]
    assert data.get("is_admin", None) == user1_credentials["is_admin"]
    assert data.get("disabled", None) == user1_credentials["disabled"]
    assert data.get("origem_unidade", None) == user1_credentials["origem_unidade"]
    assert (
        data.get("cod_unidade_autorizadora", None)
        == user1_credentials["cod_unidade_autorizadora"]
    )


# create /user
def test_create_user_not_logged_in(client: Client, header_not_logged_in: dict):
    response = client.put(
        f"/user/{USERS_TEST[0]['email']}",
        headers=header_not_logged_in,
        json=USERS_TEST[0],
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_user_logged_in_not_admin(
    client: Client, header_usr_2: dict  # user is_admin=False
):
    response = client.put(
        f"/user/{USERS_TEST[0]['email']}", headers=header_usr_2, json=USERS_TEST[0]
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_user_logged_in_admin(
    client: Client, header_usr_1: dict  # user is_admin=True
):
    response = client.put(
        f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1, json=USERS_TEST[0]
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_create_user_without_required_fields(
    client: Client, header_usr_1: dict  # user is_admin=True
):
    response = client.put(
        f"/user/{USERS_TEST[2]['email']}", headers=header_usr_1, json=USERS_TEST[2]
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_bad_email_format(
    client: Client, header_usr_1: dict  # user is_admin=True
):
    response = client.put(
        f"/user/{USERS_TEST[3]['email']}", headers=header_usr_1, json=USERS_TEST[3]
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# update /user
def test_update_user(client: Client, header_usr_1: dict):  # user is_admin=True
    # get
    r_1 = client.get(f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1)
    data_before = r_1.json()

    # update
    new_data = data_before
    new_data["cod_unidade_autorizadora"] = 99
    new_data["password"] = "new_secret"
    r_2 = client.put(
        f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1, json=new_data
    )
    assert r_2.status_code == status.HTTP_200_OK

    # get new value
    r_3 = client.get(f"/user/{USERS_TEST[0]['email']}", headers=header_usr_1)
    data_after = r_3.json()

    assert data_before.get("cod_unidade_autorizadora", None) == data_after.get(
        "cod_unidade_autorizadora", None
    )


# forgot/reset password


def get_all_mailbox_messages(
    host: str = "smtp4dev",
    user: str = "smtp4dev",
    password: str = "",
) -> Generator[email.message.Message, None, None]:
    """Get messages from the mailbox.

    Args:
        host (str, optional): IMAP connection host. Defaults to "localhost".
        user (str, optional): IMAP connection user name. Defaults to "smtp4dev".
        password (str, optional): IMAP connection password. Defaults to "".

    Raises:
        ValueError: if the mailbox can't be accessed.

    Yields:
        Iterator[email.message.Message]: each message found in the mailbox.
    """
    with IMAP4(host=host, port=143) as connection:
        connection.login(user, password)
        connection.enable("UTF8=ACCEPT")
        query_status, inbox = connection.select(readonly=True)
        if query_status != "OK":
            raise ValueError("Access to email inbox failed.")
        message_count = int(inbox[0])
        for message_index in range(message_count + 1):
            query_status, response = connection.fetch(str(message_index), "(RFC822)")
            for item in response:
                if isinstance(item, tuple):
                    yield email.message_from_bytes(item[1])


def get_latest_message_uid(messages: dict[int, email.message.Message]) -> str:
    """Get the latest message uid from the mailbox.

    Args:
        messages (dict[int,email.message.Message]): a dict containing
            the message uids for keys and the message object for values,
            representing all messages in the mailbox.

    Returns:
        str: the latest message's uid.
    """
    return max(
        (
            (datetime.strptime(message["date"], "%a, %d %b %Y %H:%M:%S %z"), index)
            for index, message in messages.items()
        )
    )[1]


def get_message_body(
    uid: int,
    host: str = "smtp4dev",
    user: str = "smtp4dev",
    password: str = "",
) -> str:
    """Given an uid, get the message's body from the IMAP server.

    Args:
        uid (int): the uid of the message.
        host (str, optional): IMAP connection host. Defaults to "localhost".
        user (str, optional): IMAP connection user name. Defaults to "smtp4dev".
        password (str, optional): IMAP connection password. Defaults to "".

    Raises:
        ValueError: _description_

    Returns:
        str: _description_
    """
    with IMAP4(host=host, port=143) as connection:
        connection.login(user, password)
        connection.enable("UTF8=ACCEPT")
        query_status, _ = connection.select(readonly=True)
        if query_status != "OK":
            raise ValueError("Access to email inbox failed.")
        query_status, response = connection.fetch(str(uid), "(RFC822)")
        message = email.message_from_bytes(response[0][1])
        content = [
            part for part in message.walk() if part.get_content_type() == "text/html"
        ][0].get_payload(decode=True)
        return content.decode("utf-8")


def get_token_from_content(content: str) -> str:
    """Get the token from the email content.

    Args:
        content (str): content of email.

    Raises:
        ValueError: if no token is found in the email.

    Returns:
        str: the access token.
    """
    match = TOKEN_IN_MESSAGE.search(content)
    if match:
        return match.group(1)
    raise ValueError("Message contains no token.")


def get_token_from_email(
    host: str = "smtp4dev",
    user: str = "smtp4dev",
    password: str = "",
) -> str:
    """Access the mailbox and get the token from the email.

    Args:
        host (str, optional): IMAP connection host. Defaults to "localhost".
        user (str, optional): IMAP connection user name. Defaults to "smtp4dev".
        password (str, optional): IMAP connection password. Defaults to "".

    Returns:
        str: the access token.
    """
    messages = dict(enumerate(get_all_mailbox_messages(host, user, password), start=1))
    latest_message = get_latest_message_uid(messages)
    return get_token_from_content(get_message_body(uid=latest_message, host=host))


def test_forgot_password(
    register_user_1,  # pylint: disable=unused-argument
    client: Client,
    user1_credentials: dict,
    header_usr_1: dict,
):
    """Tests the forgot and reset password functionality."""
    # use the forgot_password endpoint to send an email
    response = client.post(
        f"/user/forgot_password/{user1_credentials['email']}", headers=header_usr_1
    )
    assert response.status_code == status.HTTP_200_OK

    # get the token from the email
    access_token = get_token_from_email(host="smtp4dev")

    # reset the password to a new password using the received token
    new_password = "new_password_for_test"
    response = client.get(
        "/user/reset_password/",
        params={"access_token": access_token, "password": new_password},
    )
    assert response.status_code == status.HTTP_200_OK

    # test if the old credentials no longer work
    response = client.post(
        "/token",
        data={
            "username": user1_credentials["email"],
            "password": user1_credentials["password"],
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # test if the new credentials work
    response = client.post(
        "/token",
        data={
            "username": user1_credentials["email"],
            "password": new_password,
        },
    )
    assert response.status_code == status.HTTP_200_OK
