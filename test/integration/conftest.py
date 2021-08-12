from fastapi.exceptions import HTTPException
from starlette.testclient import TestClient

from main import app

client = TestClient(app)


def get_auth_header():
        response = client.post("/token", dict(username="tusker", password="tusker"))
        if response.status_code != 200:
            raise AssertionError("Authentication failure:, original error" + str(response.json()))
        jwt_token = response.json()["access_token"]
        auth_header = {"Authorization": f"Bearer {jwt_token}"}
        return auth_header

