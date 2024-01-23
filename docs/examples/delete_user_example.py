import httpx
from get_token_example import get_token

url = "http://localhost:5057/user"

def delete_user(admin_user, del_user):
    headers = {
        "accept": "application/json",
        "Authorization": f'Bearer {get_token(admin_user)}',
        "Content-Type": "application/json",
    }
    response = httpx.delete(f'{url}/{del_user["email"]}', headers=headers)
    print(f"Status Code: {response.status_code}")
    response.raise_for_status()

    return response.text

if __name__ == "__main__":
    admin_user = {
        "username": "johndoe@oi.com",
        "password": "secret",
    }
    del_user = {"email": "user@oi.com"}
    print(delete_user(admin_user, del_user))
