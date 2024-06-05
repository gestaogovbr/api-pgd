"""Testes relacionados às permissões de uso dos endpoints do Plano de
Entregas.
"""

from httpx import Client
from fastapi import status as http_status

from .core_test import assert_equal_plano_entregas


def test_get_plano_entregas_different_unit(
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    header_usr_2: dict,
    input_pe,
    client: Client,
):
    """Tenta buscar um plano de entregas existente em uma unidade diferente,
    à qual o usuário não tem acesso."""

    response = client.get(
        f"/organizacao/SIAPE/3"  # Sem autorização nesta unidade
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        headers=header_usr_2,
    )
    assert response.status_code == http_status.HTTP_403_FORBIDDEN


def test_get_plano_entregas_different_unit_admin(
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    header_admin: dict,
    input_pe,
    client: Client,
):
    """Tenta buscar um plano de entregas existente em uma unidade diferente, mas
    com um usuário com permissão de admin."""

    response = client.get(
        f"/organizacao/SIAPE/3"  # Unidade diferente
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        headers=header_admin,
    )
    assert response.status_code == http_status.HTTP_200_OK


def test_create_plano_entregas_unidade_nao_permitida(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    header_usr_2: dict,
    client: Client,
):
    """Tenta criar um novo Plano de Entregas em uma organização na qual
    ele não está autorizado.
    """
    response = client.put(
        "/organizacao/SIAPE/3"  # só está autorizado na organização 2
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_usr_2,
    )

    assert response.status_code == http_status.HTTP_401_UNAUTHORIZED
    assert (
        response.json().get("detail", None)
        == "Usuário não tem permissão na cod_unidade_autorizadora informada"
    )


def test_create_plano_entregas_outra_unidade_admin(
    truncate_pe,  # pylint: disable=unused-argument
    input_pe: dict,
    header_admin: dict,
    admin_credentials: dict,
    client: Client,
):
    """Tenta, como administrador, criar um novo Plano de Entregas em uma
    organização diferente da sua própria organização.
    """
    input_pe["cod_unidade_autorizadora"] = 3  # unidade diferente

    response = client.get(
        f"/user/{admin_credentials['username']}",
        headers=header_admin,
    )

    # Verifica se o usuário é admin e se está em outra unidade
    assert response.status_code == http_status.HTTP_200_OK
    admin_data = response.json()
    assert (
        admin_data.get("cod_unidade_autorizadora", None)
        != input_pe["cod_unidade_autorizadora"]
    )
    assert admin_data.get("is_admin", None) is True

    response = client.put(
        f"/organizacao/SIAPE/{input_pe['cod_unidade_autorizadora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega']}",
        json=input_pe,
        headers=header_admin,
    )

    assert response.status_code == http_status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert_equal_plano_entregas(response.json(), input_pe)
