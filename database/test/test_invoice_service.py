# %%
import pytest
import time
import copy
from database import crud
from database.crud.invoice_service import invoice_to_terms
from database.crud.whitelist_service import whitelist as whitelistService
from database.models import Invoice
from database.exceptions import DuplicateInvoiceException
from database.test.fixtures import NEW_RAW_ORDER, RAW_ORDER, get_new_raw_order
from database.db import SessionLocal, metadata, engine, session
from sqlalchemy.orm import Session
from invoice.tusker_client import code_to_order_status, tusker_client
from typing import Tuple
import contextlib
import json
from utils.constant import MAX_CREDIT, RECEIVER_ID1, GURUGRUPA_CUSTOMER_ID
from database.test.conftest import reset_db
import datetime as dt

invoice_service = crud.invoice
db = SessionLocal()


# %%
# @pytest.mark.skip()
def test_reset_db():
    reset_db()
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(NEW_RAW_ORDER, "p", "s", db)
    reset_db()
    after = invoice_service.get_all_invoices(db)
    assert len(after) == 0


def test_internal_insert_invoice(invoice1):
    _, db_session = invoice1
    before = invoice_service.get_all_invoices(db_session)

    invoice_id = invoice_service._insert_new_invoice_for_purchaser_x_supplier(
        NEW_RAW_ORDER,
        purchaser_id="testP",
        supplier_id="testS",
        db=db_session
    )

    after = invoice_service.get_all_invoices(db_session)

    # verify there is an extra invoice and its the one newly added
    assert len(after) == len(before) + 1
    assert invoice_id in [i.id for i in after]

    # assert properties are correctly mapped
    invoice_in_db = [i for i in after if i.id == invoice_id][0]
    assert invoice_in_db.value == NEW_RAW_ORDER.get("consgt", {}).get("val_dcl", 0)
    assert invoice_in_db.order_ref == NEW_RAW_ORDER.get('ref_no')
    assert invoice_in_db.shipment_status == "PLACED_AND_VALID"
    assert invoice_in_db.finance_status == "INITIAL"

    # check raw data is conserved
    assert json.loads(invoice_in_db.data) == NEW_RAW_ORDER
    reset_db()


def test_insert_invoice_that_exists_fail(invoice1: Tuple[Invoice, Session]):
    invoice1, db_session = invoice1
    with pytest.raises(DuplicateInvoiceException):
        invoice_service._insert_new_invoice_for_purchaser_x_supplier(
            raw_order = json.loads(invoice1.data),
            purchaser_id=invoice1.purchaser_id,
            supplier_id=invoice1.supplier_id,
            db=db
        )


def test_update_invoice_shipment_status(invoice1):
    invoice1, db_session = invoice1
    invoice_service.update_invoice_shipment_status(invoice1.id, "NEW_STATUS", db_session)
    after = invoice_service.get(db_session, invoice1.id)
    assert  after.shipment_status == "NEW_STATUS"
    reset_db()


def test_update_invoice_with_payment_terms(invoice1):
    invoice1, db_session = invoice1
    _id = invoice1.id

    before = invoice_service.get(db_session, id=_id)
    assert json.loads(before.payment_details)['interest'] != 1000

    terms = invoice_to_terms(_id, invoice1.order_ref, 'loanId1', invoice1.value, dt.datetime.now())
    terms.interest = 1000
    invoice_service.update_invoice_with_loan_terms(before, terms, db_session)

    after = invoice_service.get(db_session, id=invoice1.id)
    assert json.loads(after.payment_details)['interest'] == 1000


def test_delete_invoice(invoice1):
    invoice1, db_session = invoice1
    _id = invoice1.id

    invoice_service.remove(db_session, id=_id)

    invoice = db_session.query(Invoice).filter(Invoice.id == _id).first()
    assert not invoice


def test_get_all_invoices(invoices):
    [invoice1, invoice2], db = invoices

    _invoices = invoice_service.get_all_invoices(db)

    ids_from_db = [i.id for i in _invoices]
    assert invoice1.id in ids_from_db
    assert invoice2.id in ids_from_db

def test_update_db(invoice1):
    invoice1, db_session = invoice1
    # save current status (same as what is on tusker-api)
    tmp = invoice1.shipment_status
    # change status on db so that whatever is pulled from tusker will be new
    invoice_service.update_invoice_shipment_status(invoice1.id, "somestatus", db_session)
    before = invoice_service.get_all_invoices(db_session)[0]
    time.sleep(1)

    updated, errored = invoice_service.update_invoice_db(db_session)

    assert not errored
    assert updated[0][0] == invoice1.id
    assert updated[0][1] == tmp


    # TODO this chcek should pass
    after = invoice_service.get_all_invoices(db_session)[0]
    # assert before.updated_on < after.updated_on

    # TODO move this into its own test
    assert after.delivered_on is not None

@pytest.mark.xfail()
def test_update_db_stores_update_timestamp_and_delivered_on(invoice1):
    # save current status (same as what is on tusker-api)
    tmp = invoice1.shipment_status
    assert invoice1.shipment_status == "DELIVERED"

    # change status on db so that whatever is pulled from tusker will be new
    invoice1.shipment_status = "somestatus"
    before = invoice_service.get_all_invoices()[0]

    updated, errored = invoice_service.update_invoice_db()

    assert not errored

    after = invoice_service.get_all_invoices()[0]
    # TODO issue#32
    assert before.updated_on < after.updated_on

    assert after.delivered_on is not None


def test_update_invoices(invoice1):
    invoice1, db_session = invoice1
    assert invoice1.finance_status == "INITIAL"
    assert invoice1.shipment_status == "DELIVERED"

    invoice_service.update_invoice_payment_status(db_session, invoice1.id, "PAID")
    invoice_service.update_invoice_shipment_status(db_session, invoice1.id, "IN_TRANSIT")

    assert invoice1.finance_status == "PAID"
    assert invoice1.shipment_status == "IN_TRANSIT"

    # invoice_service.update_invoice_payment_status


@pytest.mark.skip()
def test_multiple_invoice_updates():
    # see whether
    pass


@pytest.mark.skip()
def test_update_error_reporting():
    # see whether errors are reported correctly
    pass
 

