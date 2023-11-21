"""Module for interacting with the Fief API admin interface.
"""
from functools import cached_property
import urllib
from typing import Optional
import secrets

import httpx

REQUEST_TIMEOUT = 5.0


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

    def __init__(
        self, api_token: str, base_url: str, request_timeout: str = REQUEST_TIMEOUT
    ):
        """
        Initialize the Fief_Admin_Helper class.
        """
        self.api_token = api_token
        self.base_url = base_url
        self.request_timeout = request_timeout

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
        if method in ["PATCH", "PUT"]:
            headers["Content-Type"] = "application/json"
            return httpx.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=self.request_timeout,
            )
        if method == "POST":
            headers["Content-Type"] = "application/json"
            return httpx.post(
                url=url,
                headers=headers,
                json=data,
                timeout=self.request_timeout,
            )
        return httpx.request(
            method=method,
            url=url,
            headers=headers,
            timeout=self.request_timeout,
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
            "email_verified": True,
            "fields": fields,
            "tenant_id": self.first_tenant["id"],
        }
        return self.fief_admin_call(
            method="POST",
            local_url="users/",
            data=data,
        )

    def get_user_by_email(self, email: str) -> dict:
        """Get the User's id by their email.

        Args:
            email (str): User's email.

        Returns:
            dict: User's data.
        """
        user_search = self.search_user(email=email).json()
        if user_search["count"] < 1:
            raise ValueError(f"Nenhum usuário com o e-mail {email} foi encontrado.")
        user = user_search["results"][0]
        return user

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
        user = self.get_user_by_email(email)
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
        self,
        uri: str,
        client_id: Optional[str] = None,
        remove_http: bool = False,
    ) -> httpx.Response:
        """Adds a Redirect URI to a Fief client.

        Args:
            uri (str): the redirect URI to be added.
            client_id (str, optional): the client's internal id. If None
                or omitted, will use the first client found in the API.
                Defaults to None.
            remove_http (bool, optional): if True, will first remove
                http URIs before submitting the Fief Admin API call
                (Fief will refuse the API call otherwise, unless
                CLIENT_REDIRECT_URI_SSL_REQUIRED is set to False).

        Returns:
            httpx.Response: the Response object obtained from the API
                call.
        """
        if not client_id:
            client_id = self.first_client["id"]
        client = self.get_client(client_id)
        redirect_uris = [
            existing_uri
            for existing_uri in client["redirect_uris"]
            if urllib.parse.urlparse(existing_uri).scheme == "https" or not remove_http
        ]

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

    def create_permission(self, name: str, codename: str) -> httpx.Response:
        """Create a Permission in the Fief environment.

        Args:
            name (str): Name of the Permission.
            codename (str): Codename for the Permission, such as castles:create.

        Returns:
            httpx.Response: the Response object obtained from the API
                call.
        """
        response = self.fief_admin_call(
            method="POST",
            local_url="permissions/",
            data={
                "name": name,
                "codename": codename,
            },
        )
        return response

    def get_role_by_name(self, name: str) -> dict:
        """Get a Role's data by the Role's name.

        Args:
            name (str): The Role's name.

        Returns:
            dict: Role's data.
        """
        response = self.fief_admin_call(
            method="GET",
            local_url="roles/",
        )
        response.raise_for_status()
        roles_search = response.json()
        if roles_search["count"] < 1:
            raise ValueError("Nenhuma Role encontrada.")
        role = None
        for result in roles_search["results"]:
            if result["name"] == name:
                role = result
        if role is None:
            raise ValueError(f"Nenhuma Role com o nome {name} foi encontrada.")
        return role

    def create_role(
        self, name: str, permissions: list[str], granted_by_default: bool = False
    ) -> httpx.Response:
        """Create a Role in the Fief environment.

        Args:
            name (str): Name of the Role.
            permissions (list[str]): List of respective uuid's of the
                permissions the role should have.
            granted_by_default (bool, optional): Whether the role is
                applied by default to users. Defaults to False.

        Returns:
            httpx.Response: the Response object obtained from the API
                call.
        """
        response = self.fief_admin_call(
            method="POST",
            local_url="roles/",
            data={
                "name": name,
                "granted_by_default": granted_by_default,
                "permissions": permissions,
            },
        )
        return response

    def user_grant_role(self, user_email: str, role_name: str) -> httpx.Response:
        """Grant a Role to a User.

        Args:
            user_id (str): The User's email.
            role_id (str): The Role's name.
        """
        user = self.get_user_by_email(user_email)
        role = self.get_role_by_name(role_name)
        response = self.fief_admin_call(
            method="POST",
            local_url=f"users/{user['id']}/roles",
            data={"id": role["id"]},
        )
        return response
