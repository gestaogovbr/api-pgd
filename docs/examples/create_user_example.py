import httpx
from get_token_example import USER_AGENT, get_token

URL = "http://localhost:5057/user"


def create_user(admin_user, new_user):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {get_token(admin_user)}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    response = httpx.put(f'{URL}/{new_user["email"]}', headers=headers, json=new_user)
    print(f"Status Code: {response.status_code}")
    response.raise_for_status()

    return response.text


if __name__ == "__main__":
    admin_user = {
        "username": "johndoe@oi.com",
        "password": "secret",
    }
    new_user = {
        "email": "user@oi.com",
        "password": "secret",
        # "is_admin": False, # defaults to False
        # "disabled": False, # defaults to False
        "origem_unidade": "SIAPE",
        "cod_unidade_autorizadora": 667,
        "sistema_gerador": "PGD Petrvs MGI – Ambiente próprio 2.3.2",
    }
    print("user:", create_user(admin_user, new_user))
