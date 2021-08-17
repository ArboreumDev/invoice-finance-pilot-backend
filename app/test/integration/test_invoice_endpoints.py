from test.integration.conftest import get_auth_header
from typing import Dict, Tuple

import pytest
from sqlalchemy.orm import Session
from starlette.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST,
                              HTTP_404_NOT_FOUND)
from starlette.testclient import TestClient

from database.crud.invoice_service import invoice as invoice_service
from database.crud.supplier_service import supplier as supplier_service
from database.crud.whitelist_service import whitelist as whitelist_service
from database.schemas.supplier import SupplierCreate
from database.test.conftest import (db_session, insert_base_user,  # noqa: 401
                                    reset_db)
from database.test.fixtures import p1, p2
from invoice.tusker_client import tusker_client
from main import app
from utils.common import InvoiceFrontendInfo, PurchaserInfo
from utils.constant import GURUGRUPA_CUSTOMER_ID, LOC_ID4

client = TestClient(app)
CUSTOMER_ID = "0001e776-c372-4ec5-8fa4-f30ab74ca631"


# TODO figure out why these fixtures can not be imported from the other conftest file
@pytest.fixture(scope="function")
def whitelist_and_invoices(db_session) -> Tuple[Tuple, Tuple, str, PurchaserInfo, Session, Dict]:  # noqa: F811
    reset_db(deleteWhitelist=True)
    insert_base_user(db_session)
    auth_header = get_auth_header()
    whitelist_service.insert_whitelist_entry(
        db=db_session, supplier_id=GURUGRUPA_CUSTOMER_ID, purchaser=p1, creditline_size=50000, apr=0.1, tenor_in_days=90
    )
    whitelist_service.insert_whitelist_entry(
        db=db_session, supplier_id=GURUGRUPA_CUSTOMER_ID, purchaser=p2, creditline_size=50000, apr=0.1, tenor_in_days=90
    )

    inv_id1, order_ref1, _ = tusker_client.create_test_order(
        supplier_id=GURUGRUPA_CUSTOMER_ID, location_id=p1.location_id
    )
    inv_id2, order_ref2, _ = tusker_client.create_test_order(
        supplier_id=GURUGRUPA_CUSTOMER_ID, location_id=p2.location_id
    )

    yield (inv_id1, order_ref1), (inv_id2, order_ref2), GURUGRUPA_CUSTOMER_ID, p1, db_session, auth_header

    reset_db(deleteWhitelist=True)


@pytest.fixture(scope="function")
def whitelist_entry(db_session: Session) -> Tuple[PurchaserInfo, str, Session]:  # noqa: F811
    reset_db(deleteWhitelist=True)
    insert_base_user(db_session)
    auth_header = get_auth_header()
    whitelist_service.insert_whitelist_entry(
        db_session, supplier_id=CUSTOMER_ID, purchaser=p1, creditline_size=50000, apr=0.1, tenor_in_days=90
    )
    supplier_service.create(
        db=db_session,
        obj_in=SupplierCreate(
            supplier_id=CUSTOMER_ID,
            name="TestSupplier",
            creditline_size=400000000,
            default_apr=0.142,
            default_tenor_in_days=90,
        ),
    )

    yield p1, CUSTOMER_ID, db_session, auth_header

    reset_db(deleteWhitelist=True)


# TODO add jwt-token to all requests / modify client to have a valid header by default


def test_health():
    pass


def test_invalid_credential():
    # with pytest.raises(HTTPException):
    client.get("v1/invoice")


# TODO all negative endpoint results
def test_insert_existing_invoice_failure(whitelist_and_invoices):
    _, order_ref1 = whitelist_and_invoices[0]
    db, auth_header = whitelist_and_invoices[4], whitelist_and_invoices[5]

    assert len(invoice_service.get_all_invoices(db)) == 0
    # should add new invoice to db
    res = client.post(f"v1/invoice/{order_ref1}", headers=auth_header)

    assert res.status_code == HTTP_200_OK
    assert len(invoice_service.get_all_invoices(db)) == 1

    res = client.post(f"v1/invoice/{order_ref1}", headers=auth_header)
    assert res.status_code == HTTP_400_BAD_REQUEST


def test_get_order(whitelist_and_invoices):
    _, (_, order_ref), _, _, _, auth_header = whitelist_and_invoices
    response = client.get(f"v1/order/{order_ref}", headers=auth_header)
    order = InvoiceFrontendInfo(**response.json())
    assert order.shipping_status == "PLACED_AND_VALID"


def test_whitelist_failure(whitelist_and_invoices):
    # create order for customer that is not whitelisted
    _, _, supplier_id, purchaser, _, auth_header = whitelist_and_invoices
    assert LOC_ID4 != purchaser.id

    _, order_ref, _ = tusker_client.create_test_order(supplier_id=supplier_id, location_id=LOC_ID4)

    # try querying order
    response = client.get(f"v1/order/{order_ref}", headers=auth_header)
    assert response.status_code == 400
    assert "whitelisted" in response.json()["detail"]


def test_whitelist_success(whitelist_and_invoices):
    _, (inv_id, order_ref), supplier_id, purchaser, _, auth_header = whitelist_and_invoices
    response = client.get(f"v1/order/{order_ref}", headers=auth_header)
    assert response.status_code == 200


def test_get_order_invalid_order_id(whitelist_entry):
    auth_header = whitelist_entry[3]
    response = client.get("v1/order/deadBeef", headers=auth_header)
    assert response.status_code == HTTP_404_NOT_FOUND
    assert "order id" in response.json()["detail"]


def test_add_new_invoice_success(whitelist_and_invoices):
    auth_header = whitelist_and_invoices[5]
    db = whitelist_and_invoices[4]
    assert len(invoice_service.get_all_invoices(db)) == 0
    # should add new invoice to db
    _, order_ref1 = whitelist_and_invoices[0]
    res = client.post(f"v1/invoice/{order_ref1}", headers=auth_header)
    print(res)

    assert res.status_code == HTTP_200_OK
    assert len(invoice_service.get_all_invoices(db)) == 1


@pytest.mark.xfail()
def test_add_new_invoice_failures(invoices):
    (inv_id1, order_ref1), _ = invoices
    auth_header = whitelist_and_invoices[5]
    # should reject invoices if

    #  - have invalid recipient
    # TODO

    #  - have invalid order status (e.g. already delivered)
    tusker_client.mark_test_order_as(inv_id1, "DELIVERED")

    res = client.post(f"v1/invoice/{order_ref1}", headers=auth_header)
    assert res.status_code == HTTP_400_BAD_REQUEST and "status" in res.json()["detail"]
    #  - woudl exceed credit limit
    # TODO

    #  - order is unknown
    res = client.post("v1/invoice/INVALID_ID")
    assert res.status_code == HTTP_404_NOT_FOUND and "order id" in res.json()["detail"]


def test_get_invoices_from_db(whitelist_and_invoices):
    # add invoice with order_ref to db
    inv_id1, order_ref1 = whitelist_and_invoices[0]
    auth_header = whitelist_and_invoices[5]
    client.post(f"v1/invoice/{order_ref1}", headers=auth_header)

    res = client.get("v1/invoice/", headers=auth_header)
    assert res.status_code == HTTP_200_OK
    assert res.json()[0]["orderId"] == order_ref1


# canno longer change invoice status
@pytest.mark.xfail()
def test_update_db(invoices):
    # add order to db
    # invoices, _,  auth_header = invoices
    # client.post(f"v1/invoice/{order_ref1}", headers=auth_header)

    # # read from get-invoices endpoint
    # response = client.get("v1/invoice", headers=auth_header)
    # before = InvoiceFrontendInfo(**response.json()[0]).shipping_status

    # # update order at source (tusker), then call db update
    # tusker_client.mark_test_order_as(inv_id1, "IN_TRANSIT")

    # # update
    # res = client.post("v1/invoice/update", headers=auth_header)
    # assert res.status_code == HTTP_200_OK
    # # TODO check what update returned

    # # refetch orders from get-invoice endpoint
    # response = client.get("v1/invoice", headers=auth_header)
    # assert response.status_code == HTTP_200_OK
    # InvoiceFrontendInfo(**response.json()[0]).shipping_status == "IN_TRANSIT" != before

    # # TODO should trigger finance_status updates (send email) when shipment gets delivered
    pass


# @pytest.mark.xfail()
def test_credit(whitelist_entry: Tuple[PurchaserInfo, str, Session, Dict]):
    purchaser, supplier_id, _, auth_header = whitelist_entry
    response = client.get("v1/credit", headers=auth_header)

    assert response.status_code == HTTP_200_OK

    credit_breakdown = response.json()

    assert purchaser.id in credit_breakdown[supplier_id]
