"""Module to configure a Fief instance using its admin API.
"""
import os
import sys
import argparse

sys.path.insert(0, "../src")
from fief_admin import FiefAdminHelper


def assert_not_null(env_variable: str):
    assert (
        env_variable is not None
    ), f"'{env_variable}' environment variable must be set."

# XXX can improve `get_env_vars()`?
def get_env_vars():
    fief_base_url = os.environ.get("FIEF_BASE_TENANT_URL")
    assert_not_null(fief_base_url)

    api_token = os.environ.get("FIEF_MAIN_ADMIN_API_KEY")
    assert_not_null(api_token)

    scheme = os.environ.get("WEB_URI_SCHEME")
    assert scheme in [
        "http",
        "https",
    ], "'WEB_URI_SCHEME' environment variable must be either 'http' or 'https'."

    hostname = os.environ.get("WEB_HOST_NAME")
    assert_not_null(hostname)

    port = os.environ.get("WEB_PORT")
    assert_not_null(port)

    user_email = os.environ.get("FIEF_MAIN_USER_EMAIL")
    assert_not_null(user_email)

    return fief_base_url, api_token, scheme, hostname, port, user_email


def main(is_dev: bool):
    fief_base_url, api_token, scheme, hostname, port, user_email = get_env_vars()
    # Fief admin helper object
    fief_admin = FiefAdminHelper(
        api_token=api_token,
        base_url=fief_base_url,
        request_timeout=10.0,
    )

    # ## Add clients uri
    if is_dev:
        # Add localhost swagger uri
        fief_admin.client_add_redirect_uri(
            uri=f"http://localhost:{port}/docs/oauth2-redirect",
        )

        # Add fief swagger uri
        fief_admin.client_add_redirect_uri(
            uri=f"{fief_base_url}/docs/oauth2-redirect",
        )

    # Add api-pgd container redirect uri
    fief_admin.client_add_redirect_uri(
        uri=f"{scheme}://{hostname}:{port}/docs/oauth2-redirect",
        # Fief automatically adds an http redirect URI, but then refuses to
        # PATCH the client through the API if it is left there. So it needs
        # to be manually removed.
        remove_http=(scheme == "https"),
    )

    # ## Add custom user fields
    fief_admin.create_user_field(
        name="Código SIAPE da unidade instituidora",
        slug="cod_SIAPE_instituidora",
        field_type="INTEGER",
        default_value=0,
    )

    # ## Create and Set superuser role for the admin user
    permissions = []
    r_read_all = fief_admin.create_permission("read_all", codename="all:read")
    permissions.append(r_read_all.json()["id"])

    r_write_all = fief_admin.create_permission("write_all", codename="all:write")
    permissions.append(r_write_all.json()["id"])

    fief_admin.create_role(
        "superuser", permissions=permissions, granted_by_default=False
    )

    fief_admin.user_grant_role(user_email=user_email, role_name="superuser")


if __name__ == "__main__":
    # Get script parameter
    parser = argparse.ArgumentParser(
        description="Script with optional add localhost uris for development"
    )
    parser.add_argument(
        "-dev",
        "--develop",
        action="store_true",
        help="Add localhost uris for development",
    )
    args = parser.parse_args()

    is_dev = True if args.develop else False

    main(is_dev)
