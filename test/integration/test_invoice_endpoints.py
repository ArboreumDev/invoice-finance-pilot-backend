import pytest

from database.service import invoice_service
from invoice.tusker_client import tusker_client
from database.test.conftest import reset_db
from starlette.testclient import TestClient
from main import app
from utils.common import InvoiceFrontendInfo
from starlette.status import (
    HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_200_OK
)

client = TestClient(app)

@pytest.fixture(scope="function")
def invoices():
    reset_db()
    inv_id1, order_ref1, _ = tusker_client.create_test_order()
    inv_id2, order_ref2, _ = tusker_client.create_test_order()
    yield (inv_id1, order_ref1), (inv_id2, order_ref2)
    reset_db()

# TODO add jwt-token to all requests / modify client to have a valid header by default

def test_health():
    pass

def test_invalid_credential():
    response = client.post("/token", dict(username="test", password="test"))
    pass


def test_get_order(invoices):
    response = client.get(f"v1/order/{invoices[0][1]}")
    order = InvoiceFrontendInfo(**response.json())
    assert order.shipping_status == "PLACED_AND_VALID"


def test_get_order_invalid_order_id():
    response = client.get(f"v1/order/deadBeef")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert "order id" in response.json()["detail"]


def test_add_new_invoice_success(invoices):
    assert len(invoice_service.get_all_invoices()) == 0
    # should add new invoice to db
    (_, order_ref1), _ = invoices
    client.post(f"v1/invoice/{order_ref1}")
    assert len(invoice_service.get_all_invoices()) == 1


@pytest.mark.xfail()
def test_add_new_invoice_failures(invoices):
    (inv_id1, order_ref1), _ = invoices
    # should reject invoices if 

    #  - have invalid recipient
    # TODO

    #  - have invalid order status (e.g. already delivered)
    tusker_client.mark_test_order_as(inv_id1, "DELIVERED")

    res = client.post(f"v1/invoice/{order_ref1}")
    assert res.status_code == HTTP_400_BAD_REQUEST and "status" in res.json()['detail']
    #  - woudl exceed credit limit
    # TODO

    #  - order is unknown
    res = client.post("v1/invoice/INVALID_ID")
    assert res.status_code == HTTP_404_NOT_FOUND and "order id" in res.json()['detail']


def test_get_invoices_from_db(invoices):
    # add order to db
    (inv_id1, order_ref1), _ = invoices
    client.post(f"v1/invoice/{order_ref1}")
    
    res = client.get(f"v1/invoice/")
    assert res.status_code == HTTP_200_OK
    assert res.json()[0]["orderId"] == order_ref1


def test_update_db(invoices):
    # add order to db
    (inv_id1, order_ref1), _ = invoices
    client.post(f"v1/invoice/{order_ref1}")

    # read from get-invoices endpoint
    response = client.get(f"v1/invoice")
    before = InvoiceFrontendInfo(**response.json()[0]).shipping_status

    # update order at source (tusker), then call db update
    tusker_client.mark_test_order_as(inv_id1, "IN_TRANSIT")

    # update
    res = client.post("v1/invoice/update")
    assert res.status_code == HTTP_200_OK
    # TODO check what update returned

    # refetch orders from get-invoice endpoint
    response = client.get(f"v1/invoice")
    assert response.status_code == HTTP_200_OK
    InvoiceFrontendInfo(**response.json()[0]).shipping_status == "IN_TRANSIT" != before

    # TODO should trigger finance_status updates (send email) when shipment gets delivered
