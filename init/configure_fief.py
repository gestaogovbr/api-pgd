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
    request_timeout=10.0,
)

# Add a redirect URI for API PGD
scheme = os.environ.get("WEB_URI_SCHEME")
if scheme not in ["http", "https"]:
    raise ValueError(
        "'WEB_URI_SCHEME' environment variable must be either 'http' or 'https'."
    )
hostname = os.environ.get("WEB_HOST_NAME")
if not hostname:
    raise ValueError("'WEB_HOST_NAME' environment variable must be set.")
port = os.environ.get("WEB_PORT")

# Add localhost redirect URI
# uri = f"{scheme}://localhost:{port}/docs/oauth2-redirect"
# print(f"Adding redirect URI: {uri}...")
# response = fief_admin.client_add_redirect_uri(
#     # uri=f"{scheme}://{hostname}:{port}/docs/oauth2-redirect"
#     uri=uri
# )
# print(f"Status: {response.status_code}")
# response.raise_for_status()

# Add redirect URI
uri = f"{scheme}://{hostname}/docs/oauth2-redirect"
print(f"Adding redirect URI: {uri}...")
response = fief_admin.client_add_redirect_uri(
    # uri=f"{scheme}://{hostname}:{port}/docs/oauth2-redirect"
    uri=uri,
    # Fief automatically adds an http redirect URI, but then refuses to
    # PATCH the client through the API if it is left there. So it needs
    # to be manually removed.
    remove_http=(scheme == "https"),
)
print(f"Status: {response.status_code}")
response.raise_for_status()

# Add custom user fields
print("Creating user field: cod_SIAPE_instituidora...")
response = fief_admin.create_user_field(
    name="Código SIAPE da unidade instituidora",
    slug="cod_SIAPE_instituidora",
    field_type="INTEGER",
    default_value=0,
)
print(f"Status: {response.status_code}")
response.raise_for_status()

# Create and Set superuser role for the admin user
permissions = []
print(f"Creating Permission: read_all...")
response = fief_admin.create_permission("read_all", codename="all:read")
print(f"Status: {response.status_code}")
response.raise_for_status()
permissions.append(response.json()["id"])

print(f"Creating Permission: write_all...")
response = fief_admin.create_permission("write_all", codename="all:write")
print(f"Status: {response.status_code}")
response.raise_for_status()
permissions.append(response.json()["id"])

print(f"Creating Role: superuser...")
response = fief_admin.create_role(
    "superuser", permissions=permissions, granted_by_default=False
)
print(f"Status: {response.status_code}")
response.raise_for_status()

admin_user = os.environ.get("FIEF_MAIN_USER_EMAIL")
print(f"Setting superuser flag for user: {admin_user}...")
response = fief_admin.user_grant_role(user_email=admin_user, role_name="superuser")
print(f"Status: {response.status_code}")
response.raise_for_status()
