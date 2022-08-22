"""
Testes relacionados com acessos aos endpoints.
"""

from requests import Session
from fastapi import status

def test_redirect_to_docs(client: Session):
    """
    Testa se o acesso na raiz redireciona para o /docs.
    """
    response = client.get("/", allow_redirects=False)
    assert response.status_code == status.HTTP_301_MOVED_PERMANENTLY
    assert response.headers['Location'] == "/docs"
