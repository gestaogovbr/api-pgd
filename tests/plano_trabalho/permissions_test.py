"""Testes relacionados às permissões de uso dos endpoints do Plano de
Trabalho.
"""

from httpx import Client
from fastapi import status


def test_get_pt_different_unit(
    input_pt: dict,
    header_usr_2: dict,
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    example_pt_unidade_3,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta acessar um plano de trabalho de uma unidade diferente, à
    qual o usuário não tem acesso."""
    response = client.get(
        "/organizacao/SIAPE/3"  # Sem autorização nesta unidade
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_pt_different_unit_admin(
    input_pt: dict,
    header_admin: dict,
    truncate_pt,  # pylint: disable=unused-argument
    truncate_pe,  # pylint: disable=unused-argument
    example_pe_unidade_3,  # pylint: disable=unused-argument
    example_pt_unidade_3,  # pylint: disable=unused-argument
    client: Client,
):
    """Tenta acessar um plano de trabalho de uma unidade diferente, mas
    com um usuário com permissão de admin."""
    response = client.get(
        f"/organizacao/SIAPE/3"  # Unidade diferente
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        headers=header_admin,
    )

    # Inclui os campos de resposta do json que não estavam no template
    input_pt["status"] = 3
    input_pt["cod_unidade_executora"] = 3
    input_pt["carga_horaria_disponivel"] = input_pt["carga_horaria_disponivel"]
    input_pt["avaliacao_registros_execucao"][0][
        "data_avaliacao_registros_execucao"
    ] = "2023-01-03"

    assert response.status_code == status.HTTP_200_OK
    assert_equal_plano_trabalho(response.json(), input_pt)
