"""Module to configure a Fief instance using its admin API.
"""
import os
import sys

sys.path.insert(0, "../src")
from fief_admin import FiefAdminHelper

# Fief admin helper object
fief_admin = FiefAdminHelper(
    api_token=os.environ.get("FIEF_MAIN_ADMIN_API_KEY"),
    base_url=os.environ.get("FIEF_BASE_TENANT_URL"),
)

# Add a redirect URI for API PGD
scheme = os.environ.get("FIEF_URI_SCHEME")
if scheme not in ["http", "https"]:
    raise ValueError(
        "'FIEF_URI_SCHEME' environment variable must be either 'http' or 'https'."
    )
hostname = os.environ.get("FIEF_HOST_NAME")
if not hostname:
    raise ValueError("'FIEF_HOST_NAME' environment variable must be set.")
port = os.environ.get("PORT")
response = fief_admin.client_add_redirect_uri(
    uri=f"{scheme}://{hostname}:{port}/docs/oauth2-redirect"
)
response.raise_for_status()

# Add custom user fields
response = fief_admin.create_user_field(
    name="Código SIAPE da unidade instituidora",
    slug="cod_SIAPE_instituidora",
    field_type="INTEGER",
    default_value=0,
)
response.raise_for_status()

# Set superuser field for the admin user
response = fief_admin.patch_user(
    email=os.environ.get("FIEF_MAIN_USER_EMAIL"),
    data={"is_superuser": True}
)
response.raise_for_status()
