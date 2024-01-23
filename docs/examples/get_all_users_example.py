import httpx
from get_token_example import get_token

url = 'http://localhost:5057/users'

def get_all_users(admin_user):
    headers = {
        "accept": "application/json",
        "Authorization": f'Bearer {get_token(admin_user)}',
        "Content-Type": "application/json",
    }
    response = httpx.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    response.raise_for_status()

    return response.text

if __name__ == "__main__":
    admin_user = {
        "username": "johndoe@oi.com",
        "password": "secret",
    }
    print("users:", get_all_users(admin_user))
