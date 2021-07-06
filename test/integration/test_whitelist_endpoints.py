
from test.integration.conftest import get_auth_header

import pytest
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from starlette.testclient import TestClient

from database.test.conftest import reset_db
from main import app
from routes.v1.whitelist import WhitelistInput
from utils.common import PurchaserInfo

client = TestClient(app)
AUTH_HEADER = get_auth_header()

new_whitelist_entry = WhitelistInput(
    supplier_id="s1",
    purchaser=PurchaserInfo(id="p1", name="purchaser", city="mumbai", phone="1243", location_id="Loc1"),
    creditline_size=50000,
    apr=0.1,
    tenor_in_days=90,
).dict()


@pytest.fixture(scope="function")
def clean_db():
    reset_db(deleteWhitelist=True)
    yield
    reset_db(deleteWhitelist=True)


def test_post_new_whitelist_entry_success(clean_db):
    response = client.post("v1/whitelist/new", json={"input": new_whitelist_entry}, headers=AUTH_HEADER)
    assert response.status_code == HTTP_200_OK
    # TODO verify new entry is in creditline


def test_post_new_whitelist_duplicate_entry_failure(clean_db):
    response = client.post("v1/whitelist/new", json={"input": new_whitelist_entry}, headers=AUTH_HEADER)
    assert response.status_code == HTTP_200_OK
    response = client.post("v1/whitelist/new", json={"input": new_whitelist_entry}, headers=AUTH_HEADER)
    assert response.status_code == HTTP_400_BAD_REQUEST
