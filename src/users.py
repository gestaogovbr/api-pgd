"""Objetos para acesso à gestão de usuários fornecida pela ferramenta
Fief: https://docs.fief.dev/
"""

import os

from fastapi.security import OAuth2AuthorizationCodeBearer

from fief_client import FiefAsync
from fief_client.integrations.fastapi import FiefAuth

FIEF_BASE_TENANT_URL = os.environ["FIEF_BASE_TENANT_URL"]
FIEF_CLIENT_ID = os.environ["FIEF_CLIENT_ID"]
FIEF_CLIENT_SECRET = os.environ["FIEF_CLIENT_SECRET"]

fief = FiefAsync(
    base_url=FIEF_BASE_TENANT_URL,
    client_id=FIEF_CLIENT_ID,
    client_secret=FIEF_CLIENT_SECRET,
)

scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{FIEF_BASE_TENANT_URL}/authorize",
    tokenUrl=f"{FIEF_BASE_TENANT_URL}/api/token",
    scopes={"openid": "openid"},
    auto_error=False,
)

auth_backend = FiefAuth(fief, scheme)
