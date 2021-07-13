from test.integration.conftest import get_auth_header

import pytest
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from starlette.testclient import TestClient

from database.test.conftest import insert_base_user, reset_db
from database.whitelist_service import whitelist_service
from main import app
from routes.v1.whitelist import WhitelistInput, WhitelistUpdateInput
from utils.common import PurchaserInfo, Terms

client = TestClient(app)
insert_base_user()
AUTH_HEADER = get_auth_header()

new_whitelist_entry = WhitelistInput(
    supplier_id="s1",
    purchaser=PurchaserInfo(
        id="p1",
        name="purchaser",
        city="mumbai",
        phone="1243",
        location_id="Loc1",
        terms=Terms(creditline_size=50000, apr=0.1, tenor_in_days=90),
    ),
).dict()


@pytest.fixture(scope="function")
def clean_db():
    reset_db(deleteWhitelist=True)
    insert_base_user()
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


def test_whitelist_update(clean_db):
    response = client.post("v1/whitelist/new", json={"input": new_whitelist_entry}, headers=AUTH_HEADER)
    assert response.status_code == HTTP_200_OK

    supplier_id = new_whitelist_entry["supplier_id"]
    purchaser_id = new_whitelist_entry["purchaser"]["id"]
    new_creditline_size = 40000
    new_apr = 0.2
    # new_tenor = 90

    w_before = whitelist_service.get_whitelist_entry(supplier_id, purchaser_id)
    assert w_before.apr != new_creditline_size
    assert w_before.apr != new_apr
    # assert w_before.tenor_in_days != new_tenor

    update = WhitelistUpdateInput(
        supplier_id=supplier_id,
        purchaser_id=purchaser_id,
        creditline_size=new_creditline_size,
        apr=new_apr,
        # tenor_in_days=90,
    ).dict()

    response = client.post("v1/whitelist/update", json={"update": update}, headers=AUTH_HEADER)
    assert response.status_code == HTTP_200_OK

    w = whitelist_service.get_whitelist_entry(supplier_id, purchaser_id)
    assert w.creditline_size == new_creditline_size
    assert w.apr == new_apr
    assert w.tenor_in_days == w_before.tenor_in_days


@pytest.mark.skip()
def test_whitelist_update_fail_unknown_whitelist(clean_db):
    pass


@pytest.mark.skip()
def test_whitelist_update_fail_invalid_params(clean_db):
    pass
