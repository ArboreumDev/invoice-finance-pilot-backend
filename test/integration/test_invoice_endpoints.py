import pytest

from database.service import invoice_service
from invoice.tusker_client import tusker_client
from database.test.conftest import reset_db
from starlette.testclient import TestClient
from main import app
from utils.common import InvoiceFrontendInfo
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

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
    data = response.json()
    assert data.status_code == HTTP_404_NOT_FOUND



def test_update_db(invoices):
    # should reflect shipment updates
    # should trigger finance_status updates (send email) when shipment gets delivered

    response = client.get(f"v1/order/{invoices[0][1]}")
    order = InvoiceFrontendInfo(**response.json())
    assert order.shipping_status == "PLACED_AND_VALID"

    response = client.post("v1/invoice/update")


    pass

def test_add_new_invoice_success(invoices):
    # should add new invoice to db
    pass

@pytest.mark.skip()
def test_add_new_invoice_failures(invoices):
    # should reject invoices if 
    #  - have invalid recipient
    #  - have invalid order status (e.g. already delivered)
    #  - woudl exceed credit limit
    pass

@pytest.mark.skip()
def test_get_all_orders(invoices):
    pass
# def test_add_new_invoice_success(invoices):
#     # should add new invoice to db
#     pass


