"""Funções de utilidade comum.
"""

import calendar
from datetime import date, timedelta

from fastapi import status, HTTPException
from httpx import Response


def over_a_year(start: date, end: date) -> int:
    """Calculates wether or not the period from `start` to `end` comprises
    less, equal or more than a year.

    Args:
        start (date): the beginning of the interval.
        end (date): the beginning of the interval.

    Returns:
        int: -1 if less than a year, 0 if exactly a year, 1 if more than
            a year.
    """
    add_leap = 0
    if calendar.isleap(start.year) and start.month < 3:
        add_leap = add_leap + 1
    if calendar.isleap(end.year) and end.month > 3:
        add_leap = add_leap + 1
    if end - start == timedelta(days=365 + add_leap):
        return 0
    if end - start > timedelta(days=365 + add_leap):
        return 1
    return -1


def assert_error_message(response: Response, detail_message: str):
    """Verifica se a resposta contém uma mensagem de erro específica.

    Args:
        response (Response): o objeto HTTP de resposta.
        detail_message (str): a mensagem de erro.
    """
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert any(
        (
            detail_message
            if isinstance(error, str)
            else f"Value error, {detail_message}" in error["msg"]
        )
        for error in response.json().get("detail")
    )


def check_permissions(
    origem_unidade: str, cod_unidade_autorizadora: int, user: "UsersSchema"
):
    """Verifica se o usuário possui permissões para acessar a API.

    Args:
        origem_unidade (str): origem do código da unidade.
        cod_unidade_autorizadora (int): código da unidade autorizadora.
        user (UsersSchema): informações do usuário.
    """
    if user.is_admin:
        return
    if (
        origem_unidade != user.origem_unidade
        or cod_unidade_autorizadora != user.cod_unidade_autorizadora
    ) and not user.is_admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Usuário não tem permissão na cod_unidade_autorizadora informada",
        )
