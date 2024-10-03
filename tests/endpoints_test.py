"""
Testes relacionados com acessos aos endpoints.
"""

from typing import Optional

from fastapi import status
from httpx import Client
import pytest

from .conftest import TEST_USER_AGENT

# Entrypoint da API e redirecionamentos


def test_redirect_to_docs_html(client: Client):
    """Testa se o acesso por um navegador na raiz redireciona para o /docs."""
    response = client.get("/", follow_redirects=False, headers={"Accept": "text/html"})

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"] == "/docs"


def test_redirect_to_entrypoint_json(client: Client):
    """Testa se o acesso por um script na raiz redireciona para o /openapi.json."""
    response = client.get(
        "/", follow_redirects=False, headers={"Accept": "application/json"}
    )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"] == "/openapi.json"


# Teste de cabeçalho User-Agent


@pytest.mark.parametrize(
    "user_agent",
    [
        None,
        TEST_USER_AGENT,
    ],
)
def test_user_agent_header(
    truncate_participantes,  # pylint: disable=unused-argument
    example_part,  # pylint: disable=unused-argument
    user_agent: Optional[str],
    input_part,
    header_usr_1,
    client: Client,
):
    """Testa efetuar requisições com e sem o cabeçalho user-agent."""
    headers = header_usr_1.copy()
    user_agent = headers["User-Agent"] or ""

    response = client.get(
        f"/organizacao/SIAPE/{input_part['cod_unidade_autorizadora']}"
        f"/{input_part['cod_unidade_lotacao']}"
        f"/participante/{input_part['matricula_siape']}",
        headers=headers,
    )

    if user_agent:
        assert response.status_code == status.HTTP_200_OK
    else:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "User-Agent header is required"
