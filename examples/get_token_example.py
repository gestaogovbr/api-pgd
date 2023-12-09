import httpx

url = "http://localhost:5057/token"

def get_token(data):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    with httpx.Client() as client:
        response = client.post(url, headers=headers, data=data)
        print(f"Status Code: {response.status_code}")
        response.raise_for_status()
        access_token = response.json()["access_token"]

        return access_token

if __name__ == "__main__":
    # em ../docker-compose.yml
    data = {
        "username": "johndoe@oi.com", # API_PGD_ADMIN_USER
        "password": "secret", # API_PGD_ADMIN_PASSWORD
    }
    print("token:", get_token(data))

