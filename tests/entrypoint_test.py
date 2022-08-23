"""
Testes relacionados com acessos aos endpoints.
"""

from requests import Session
from fastapi import status
import pytest

def test_redirect_to_docs_html(client: Session):
    """
    Testa se o acesso por um navegador na raiz redireciona para o /docs.
    """
    response = client.get("/",
        allow_redirects=False,
        headers={"Accept": "text/html"})

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers['Location'] == "/docs"

def test_redirect_to_entrypoint_json(client: Session):
    """
    Testa se o acesso por um script na raiz redireciona para o /openapi.json.
    """
    response = client.get("/",
        allow_redirects=False,
        headers={"Accept": "application/json"})

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers['Location'] == "/openapi.json"
