import pytest

from database.service import invoice_service
from invoice.utils.tusker_client import tusker_client
from database.test.conftest import reset_db
from starlette.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture(scope="function")
def invoices():
    reset_db()
    inv_id1, order_ref1, _ = tusker_client.create_test_order()
    inv_id2, order_ref2, _ = tusker_client.create_test_order()
    # somehow its odd not to have proper types to be passing around
    invoices = {
        inv_id1: order_ref1,
        inv_id2: order_ref2
    }
    yield invoices
    reset_db()

# TODO add jwt-token to all requests / modify client to have a valid header by default

def test_health():
    pass

def test_invalid_credential():
    response = client.post("/token", dict(username="test", password="test"))
    pass

def test_get_order(invoices):
    pass

def test_get_all_orders(invoices):
    pass

def test_update_db(invoices):
    # should reflect shipment updates
    # should trigger finance_status updates (send email) when shipment gets delivered
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

def test_add_new_invoice_success(invoices):
    # should add new invoice to db
    pass


