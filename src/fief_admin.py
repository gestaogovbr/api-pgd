"""Module for interacting with the Fief API admin interface.
"""
from functools import cached_property
import urllib
from typing import Optional
import secrets

import httpx


class FiefAdminHelper:
    """
    A helper class for interacting with the Fief API using admin authentication.

    Attributes:
        api_token (str): The API token for admin authentication.
        base_url (str): The base URL for the Fief API.

    Methods:
        fief_admin_call(method, local_url, params=None, data=None):
            Calls the Fief API with an admin token.
        get_fief_tenant():
            Get the tenant id for the first tenant registered in Fief.
        get_fief_client():
            Get the client id for the first client registered in Fief.
        register_user(email, password, cod_unidade):
            Registers a new user in Fief.
    """

    def __init__(self, api_token: str, base_url: str):
        """
        Initialize the Fief_Admin_Helper class.
        """
        self.api_token = api_token
        self.base_url = base_url

    def fief_admin_call(
        self,
        method: str,
        local_url: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> httpx.Response:
        """
        Calls the Fief API with an admin token.

        Args:
            method (str): HTTP method to use.
            local_url (str): The local part of the URL.
            params (dict, optional): Parameters for the URL. Defaults to None.
            data (dict, optional): Dictionary to post. Defaults to None.

        Returns:
            httpx.Response: The Response object returned by the API call.
        """
        url = f"{self.base_url}/admin/api/{local_url}"
        if params:
            url += f"?{urllib.parse.urlencode(params)}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }
        if method in ["PATCH", "POST", "PUT"]:
            headers["Content-Type"] = "application/json"
            return httpx.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
            )
        return httpx.request(
            method=method,
            url=url,
            headers=headers,
        )

    @cached_property
    def first_tenant(self) -> dict:
        """
        Get data for the first tenant registered in Fief.

        Returns:
            dict: The tenant data returned by the Fief admin API.
        """
        return self.fief_admin_call(
            method="GET",
            local_url="tenants/",
            params={"limit": 1, "skip": 0},
        ).json()["results"][0]

    @cached_property
    def first_client(self) -> dict:
        """
        Get data for the first client registered in Fief.

        Returns:
            dict: The client data returned by the Fief admin API.
        """
        return self.fief_admin_call(
            method="GET",
            local_url="clients/",
            params={"tenant": self.first_tenant["id"]},
        ).json()["results"][0]

    def search_user(self, email: Optional[str] = None) -> httpx.Response:
        """Search users."""
        return self.fief_admin_call(
            method="GET", local_url="users/", params={"email": email}
        )

    def register_user(
        self,
        email: str,
        cod_SIAPE_instituidora: int,
        password: Optional[str] = None,
        is_superuser: bool = False,
    ):
        """
        Registers a new user in Fief.

        Args:
            email (str): User's email.
            password (str): User's password. If omitted, a random
                password will be generated.
            cod_SIAPE_instituidora (int): User's organizational unit code.

        Returns:
            httpx.Response: The Response object returned by API call.
        """
        fields = {"cod_SIAPE_instituidora": cod_SIAPE_instituidora}
        if password is None:
            password = secrets.token_urlsafe()
        data = {
            "email": email,
            "password": password,
            "is_active": True,
            "is_superuser": is_superuser,
            "is_verified": False,
            "fields": fields,
            "tenant_id": self.first_tenant["id"],
        }
        return self.fief_admin_call(
            method="POST",
            local_url="users/",
            data=data,
        )

    def patch_user(self, email: str, data: dict) -> httpx.Response:
        """Changes one or more properties of a given user.

        Args:
            email (str): User's email.
            data (dict): User's data structure to change.
                See Fief's admin Swagger interface for an example.
                https://docs.fief.dev/api/#openapi-swagger

        Returns:
            httpx.Response: The Response object returned by API call.
        """
        user_search = self.search_user(email=email).json()
        if user_search["count"] < 1:
            raise ValueError(f"Nenhum usuário com o e-mail {email} foi encontrado.")
        user = user_search["results"][0]
        return self.fief_admin_call(
            method="PATCH",
            local_url=f"users/{user['id']}",
            data=data,
        )

    def delete_user(self, email: str) -> httpx.Response:
        """Deletes an existing user with the specified email.

        Args:
            email (str): User's email.

        Raises:
            ValueError: If no user with the given email was found.

        Returns:
            httpx.Response: The Response object returned by API call.
        """
        user_search = self.search_user(email=email).json()
        if user_search["count"] < 1:
            raise ValueError(f"Nenhum usuário com o e-mail {email} foi encontrado.")
        user = user_search["results"][0]
        return self.fief_admin_call(
            method="DELETE",
            local_url=f"users/{user['id']}",
        )

    def get_client(self, client_id: str) -> dict:
        """Obtain client data from the Fief admin API.

        Args:
            client_id (str): the client's internal id.

        Returns:
            dict: the client data returned by the Fief admin API.
        """
        return self.fief_admin_call(
            method="GET",
            local_url=f"clients/{client_id}",
        ).json()

    def client_add_redirect_uri(
        self, uri: str, client_id: Optional[str] = None
    ) -> httpx.Response:
        """Adds a Redirect URI to a Fief client.

        Args:
            uri (str): the redirect URI to be added.
            client_id (str, optional): the client's internal id. If None
            or omitted, will use the first client found in the API.
            Defaults to None.

        Returns:
            httpx.Response: the Response object obtained from the API
                call.
        """
        if not client_id:
            client_id = self.first_client["id"]
        client = self.get_client(client_id)
        redirect_uris = client["redirect_uris"]

        # remove http URIs that are not localhost (will be rejected by
        # Fief's API otherwise)
        for uri_string in redirect_uris:
            existing_uri = urllib.parse.urlparse(uri_string)
            if existing_uri.scheme == "http" and existing_uri.hostname != "localhost":
                redirect_uris.remove(uri_string)

        redirect_uris.append(uri)
        data = {
            "redirect_uris": redirect_uris,
        }
        return self.fief_admin_call(
            method="PATCH",
            local_url=f"clients/{client_id}",
            data=data,
        )

    def create_user_field(
        self,
        name: str,
        slug: str,
        field_type: str,
        default_value,
        ask_at_registration: bool = False,
        ask_at_update: bool = False,
        required: bool = False,
    ) -> httpx.Response:
        """Creates a user field in Fief.

        See documentation at
        https://docs.fief.dev/configure/user-fields/

        Args:
            name (str): Label shown on the Fief interface.
            slug (str): Field identifier used in the API.
            field_type (str): Type for the field. Check Fief API docs
                for allowed types.
            default_value (_type_): Default value for the field.
            ask_at_registration (bool, optional): Whether or not to ask
                the user to fill this field when registering.
                Defaults to False.
            ask_at_update (bool, optional): Whether or not to ask the user
                to fill this field when updating their profile.
                Defaults to False.
            required (bool, optional): Whether or not the field is required
                when presented in forms.
                Defaults to False.

         Returns:
            httpx.Response: the Response object obtained from the API
                call.
        """
        data = {
            "name": name,
            "slug": slug,
            "type": field_type,
            "configuration": {
                "default": default_value,
                "at_registration": ask_at_registration,
                "at_update": ask_at_update,
                "required": required,
            },
        }
        return self.fief_admin_call(
            method="POST",
            local_url="user-fields/",
            data=data,
        )

    def get_access_token_for_user(
        self,
        email: str,
        client_id: Optional[str] = None,
        scopes: Optional[list[str]] = None,
    ) -> str:
        """Gets an access token for the user with the specified email
        address.

        This can be used for authenticating users in automated tests.

        Args:
            email (str): email address for the user.
            client_id (str, optional): the client's id. If omitted, the
                first available client is assumed.
            scopes (list, optional): a list of scopes. If omitted, just
                "openid" is assumed.

        Returns:
            str: the access token.
        """
        if not client_id:
            client_id = self.first_client["id"]
        if not scopes:
            scopes = ["openid"]
        user_search = self.search_user(email=email).json()
        if user_search["count"] < 1:
            raise ValueError(f"Nenhum usuário com o e-mail {email} foi encontrado.")
        user = user_search["results"][0]
        response = self.fief_admin_call(
            method="POST",
            local_url=f"users/{user['id']}/access-token",
            data={"id": user["id"], "client_id": client_id, "scopes": ["openid"]},
        ).json()
        assert response["token_type"] == "bearer"
        return response["access_token"]
