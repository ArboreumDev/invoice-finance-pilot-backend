import os

import pytest
from starlette.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST,
                              HTTP_404_NOT_FOUND)
from starlette.testclient import TestClient

from database.service import invoice_service
from database.test.conftest import reset_db
from database.whitelist_service import whitelist_service
from invoice.tusker_client import tusker_client
from main import app
from utils.common import InvoiceFrontendInfo
from utils.constant import GURUGRUPA_CUSTOMER_ID, LOC_ID4

client = TestClient(app)


@pytest.fixture(scope="function")
def invoices():
    reset_db()
    whitelisted_receiver = whitelist_service.get_whitelisted_receivers(GURUGRUPA_CUSTOMER_ID)[0]
    inv_id1, order_ref1, _ = tusker_client.create_test_order(
        customer_id=GURUGRUPA_CUSTOMER_ID, location_id=whitelisted_receiver.location_id
    )
    inv_id2, order_ref2, _ = tusker_client.create_test_order(
        customer_id=GURUGRUPA_CUSTOMER_ID, location_id=whitelisted_receiver.location_id
    )
    yield (inv_id1, order_ref1), (inv_id2, order_ref2)
    reset_db()


def get_auth_header():
    response = client.post("/token", dict(username="gurugrupa", password=os.getenv("GURUGRUPA_PW")))
    jwt_token = response.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {jwt_token}"}
    return auth_header


AUTH_HEADER = get_auth_header()

# TODO add jwt-token to all requests / modify client to have a valid header by default


def test_health():
    pass


def test_invalid_credential():
    # with pytest.raises(HTTPException):
    client.get("v1/invoice")


# TODO all negative endpoint results
@pytest.mark.skip()
def test_insert_existing_invoice_failure():
    pass


def test_get_order(invoices):
    response = client.get(f"v1/order/{invoices[0][1]}", headers=AUTH_HEADER)
    order = InvoiceFrontendInfo(**response.json())
    assert order.shipping_status == "PLACED_AND_VALID"


def test_whitelist_failure():
    # create order for customer that is not whitelisted
    _, order_ref, _ = tusker_client.create_test_order(customer_id=GURUGRUPA_CUSTOMER_ID, location_id=LOC_ID4)

    # try querying order
    response = client.get(f"v1/order/{order_ref}", headers=AUTH_HEADER)
    assert response.status_code == 400


def test_whitelist_success():
    # create order for customer that is whitelisted
    whitelisted_receiver = whitelist_service.get_whitelisted_receivers(GURUGRUPA_CUSTOMER_ID)[0]
    _, order_ref, _ = tusker_client.create_test_order(
        customer_id=GURUGRUPA_CUSTOMER_ID, 
        location_id=whitelisted_receiver.location_id
    )

    # try querying order
    # order_ref = 10637833
    response = client.get(f"v1/order/{order_ref}", headers=AUTH_HEADER)
    assert response.status_code == 200


def test_get_order_invalid_order_id():
    response = client.get("v1/order/deadBeef", headers=AUTH_HEADER)
    assert response.status_code == HTTP_404_NOT_FOUND
    assert "order id" in response.json()["detail"]


def test_add_new_invoice_success(invoices):
    assert len(invoice_service.get_all_invoices()) == 0
    # should add new invoice to db
    (_, order_ref1), _ = invoices
    client.post(f"v1/invoice/{order_ref1}", headers=AUTH_HEADER)
    assert len(invoice_service.get_all_invoices()) == 1


@pytest.mark.xfail()
def test_add_new_invoice_failures(invoices):
    (inv_id1, order_ref1), _ = invoices
    # should reject invoices if

    #  - have invalid recipient
    # TODO

    #  - have invalid order status (e.g. already delivered)
    tusker_client.mark_test_order_as(inv_id1, "DELIVERED")

    res = client.post(f"v1/invoice/{order_ref1}", headers=AUTH_HEADER)
    assert res.status_code == HTTP_400_BAD_REQUEST and "status" in res.json()["detail"]
    #  - woudl exceed credit limit
    # TODO

    #  - order is unknown
    res = client.post("v1/invoice/INVALID_ID")
    assert res.status_code == HTTP_404_NOT_FOUND and "order id" in res.json()["detail"]


def test_get_invoices_from_db(invoices):
    # add order to db
    (inv_id1, order_ref1), _ = invoices
    client.post(f"v1/invoice/{order_ref1}", headers=AUTH_HEADER)

    res = client.get("v1/invoice/", headers=AUTH_HEADER)
    assert res.status_code == HTTP_200_OK
    assert res.json()[0]["orderId"] == order_ref1


# canno longer change invoice status
@pytest.mark.xfail()
def test_update_db(invoices):
    # add order to db
    (inv_id1, order_ref1), _ = invoices
    client.post(f"v1/invoice/{order_ref1}", headers=AUTH_HEADER)

    # read from get-invoices endpoint
    response = client.get("v1/invoice", headers=AUTH_HEADER)
    before = InvoiceFrontendInfo(**response.json()[0]).shipping_status

    # update order at source (tusker), then call db update
    tusker_client.mark_test_order_as(inv_id1, "IN_TRANSIT")

    # update
    res = client.post("v1/invoice/update", headers=AUTH_HEADER)
    assert res.status_code == HTTP_200_OK
    # TODO check what update returned

    # refetch orders from get-invoice endpoint
    response = client.get("v1/invoice", headers=AUTH_HEADER)
    assert response.status_code == HTTP_200_OK
    InvoiceFrontendInfo(**response.json()[0]).shipping_status == "IN_TRANSIT" != before

    # TODO should trigger finance_status updates (send email) when shipment gets delivered


def test_credit():
    response = client.get("v1/credit", headers=AUTH_HEADER)

    assert response.status_code == HTTP_200_OK

    credit_breakdown = response.json()
    whitelist_ids = whitelist_service.get_whitelisted_locations_for_customer(GURUGRUPA_CUSTOMER_ID)

    assert whitelist_ids[0] in credit_breakdown and whitelist_ids[1] in credit_breakdown
