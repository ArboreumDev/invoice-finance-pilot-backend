import os

from starlette.testclient import TestClient

from main import app

client = TestClient(app)


def get_auth_header():
    response = client.post("/token", dict(username="gurugrupa", password=os.getenv("GURUGRUPA_PW")))
    jwt_token = response.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {jwt_token}"}
    return auth_header


AUTH_HEADER = get_auth_header()
