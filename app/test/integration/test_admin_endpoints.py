from test.integration.conftest import get_auth_header
from typing import Dict, Tuple

import pytest
from database.crud.invoice_service import invoice as invoice_service
from database.crud.supplier_service import supplier as supplier_service
from database.crud.whitelist_service import whitelist as whitelist_service
from database.models import User
from database.schemas.supplier import SupplierCreate
from database.test.conftest import (db_session, insert_base_user,  # noqa: 401
                                    reset_db)
from database.test.fixtures import p1
from invoice.tusker_client import tusker_client
from main import app
from sqlalchemy.orm import Session
from starlette.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST,
                              HTTP_401_UNAUTHORIZED)
from starlette.testclient import TestClient
from utils.common import PurchaserInfo
from utils.constant import GURUGRUPA_CUSTOMER_ID

client = TestClient(app)
CUSTOMER_ID = "0001e776-c372-4ec5-8fa4-f30ab74ca631"


def insert_admin_user(db: Session):
    tusker_user = User(
        email="tusker@mail.india",
        username="admin",
        hashed_password="$2b$12$8t8LDzm.Ag68n6kv8pZoI.Oqd1x1rczNfe8QUcZwp6wnX8.dse0Ni",  # pw=tusker
        role="loanAdmin",
    )
    # TODO use crudUser
    db.add(tusker_user)
    db.commit()


# TODO figure out why these fixtures can not be imported from the other conftest file
@pytest.fixture(scope="function")
def whitelist_and_invoices(db_session) -> Tuple[Tuple, Tuple, str, PurchaserInfo, Session, Dict]:  # noqa: F811
    reset_db(db_session)
    insert_admin_user(db_session)
    auth_header = get_auth_header(username="admin", password="tusker")
    supplier_service.create(
        db=db_session,
        obj_in=SupplierCreate(
            supplier_id=GURUGRUPA_CUSTOMER_ID,
            name="TestSupplier",
            creditline_size=400000000,
            default_apr=0.142,
            default_tenor_in_days=90,
            data="",
        ),
    )

    whitelist_service.insert_whitelist_entry(
        db=db_session, supplier_id=GURUGRUPA_CUSTOMER_ID, purchaser=p1, creditline_size=50000, apr=0.1, tenor_in_days=90
    )
    inv_id1, order_ref1, _ = tusker_client.create_test_order(
        supplier_id=GURUGRUPA_CUSTOMER_ID, location_id=p1.location_id
    )

    # finance an invoice
    res = client.post(f"v1/invoice/{order_ref1}", headers=auth_header)
    assert res.status_code == HTTP_200_OK

    yield (inv_id1, order_ref1), GURUGRUPA_CUSTOMER_ID, p1, db_session, auth_header

    reset_db(db_session)


def test_admin_update_value_success(whitelist_and_invoices):
    (inv_id1, order_ref1), GURUGRUPA_CUSTOMER_ID, p1, db, auth_header = whitelist_and_invoices

    # should add new invoice to db
    invoices = invoice_service.get_all_invoices(db)
    assert len(invoices) == 1
    value_before = invoices[0].value

    res = client.post("v1/admin/update", json={"update": {"invoice_id": inv_id1, "new_value": 42}}, headers=auth_header)
    assert res.status_code == HTTP_200_OK

    db.refresh(invoices[0])
    after = invoice_service.get_all_invoices(db)[0]
    assert after.value == 42 != value_before


def to_financed_update(inv_id):
    return {
        "update": {
            "invoice_id": inv_id,
            "new_status": "FINANCED",
            "loan_id": "l1",
            "tx_id": "tx1",
            "disbursal_date": "2021-09-24T17:21:59.738443+02:00",
        }
    }


def test_admin_updates_to_financed_success(whitelist_and_invoices):
    (inv_id1, order_ref1), GURUGRUPA_CUSTOMER_ID, p1, db, auth_header = whitelist_and_invoices

    # should add new invoice to db
    invoices = invoice_service.get_all_invoices(db)
    assert len(invoices) == 1

    res = client.post(
        "v1/admin/update",
        json=to_financed_update(inv_id1),
        headers=auth_header,
    )
    assert res.status_code == HTTP_200_OK

    db.refresh(invoices[0])
    after = invoice_service.get_all_invoices(db)[0]
    assert after.finance_status == "FINANCED"
    assert "l1" in after.payment_details
    assert "tx1" in after.payment_details


def test_admin_updates_to_financed_invalid_date_failure(whitelist_and_invoices):
    (inv_id1, order_ref1), GURUGRUPA_CUSTOMER_ID, p1, db, auth_header = whitelist_and_invoices

    # should add new invoice to db
    invoices = invoice_service.get_all_invoices(db)
    assert len(invoices) == 1

    update = to_financed_update(inv_id1)
    update["update"]["disbursal_date"] = "deadbeef"

    res = client.post(
        "v1/admin/update",
        json={"update": {"invoice_id": inv_id1, "new_status": "FINANCED", "loan_id": "l1", "tx_id": "tx1"}},
        headers=auth_header,
    )
    assert res.status_code == HTTP_400_BAD_REQUEST


def test_only_admin_can_update(db_session: Session):  # noqa: F811
    reset_db(db_session)
    insert_base_user(db_session)
    auth_header = get_auth_header()

    res = client.post("v1/admin/update", json={"update": {"invoice_id": "id1"}}, headers=auth_header)

    assert res.status_code == HTTP_401_UNAUTHORIZED
