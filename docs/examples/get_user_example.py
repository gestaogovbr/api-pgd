import httpx
from get_token_example import USER_AGENT, get_token

URL = "http://localhost:5057/user"


def get_user(admin_user, user):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {get_token(admin_user)}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    response = httpx.get(f"{URL}/{user}", headers=headers)
    print(f"Status Code: {response.status_code}")
    response.raise_for_status()

    return response.text


if __name__ == "__main__":
    admin_user = {
        "username": "johndoe@oi.com",
        "password": "secret",
    }
    user = "johndoe@oi.com"
    print("user:", get_user(admin_user, user))
