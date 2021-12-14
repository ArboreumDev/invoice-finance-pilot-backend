# %%
import pytest
import time
from database import crud
from database.crud.invoice_service import invoice_to_terms
from database.models import Invoice
from database.exceptions import DuplicateInvoiceException
from database.test.fixtures import NEW_RAW_ORDER
from sqlalchemy.orm import Session
from typing import Tuple
import json
from database.test.conftest import db_session
from database.utils import reset_db
from test.integration.conftest import TestingSessionLocal
import datetime as dt
from utils.constant import MAX_CREDIT, RECEIVER_ID1, GURUGRUPA_CUSTOMER_ID
from utils.common import FinanceStatus

invoice_service = crud.invoice


# %%
# @pytest.mark.skip()
def test_reset_db(supplier_entry):
    supplier, db_session = supplier_entry
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(NEW_RAW_ORDER, "p", supplier.supplier_id, 0.32, 90, db_session)
    reset_db(db_session)
    after = invoice_service.get_all_invoices(db_session)
    assert len(after) == 0

def test_reset_db_specific(supplier_entry):
    supplier, db_session = supplier_entry
    # with tables-parameter
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(NEW_RAW_ORDER, "p", supplier.supplier_id,0.32, 90, db_session)
    reset_db(db_session, tables=["invoice"])
    after = invoice_service.get_all_invoices(db_session)
    assert len(after) == 0


def test_internal_insert_invoice(invoice_x_supplier):
    invoice, db_session = invoice_x_supplier
    before = invoice_service.get_all_invoices(db_session)
    invoice_id = invoice_service._insert_new_invoice_for_purchaser_x_supplier(
        NEW_RAW_ORDER,
        purchaser_id="testP",
        supplier_id=invoice.supplier_id,
        apr=.33,
        tenor_in_days=90,
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
    assert invoice_in_db.finance_status == FinanceStatus.INITIAL

    # check raw data is conserved
    assert json.loads(invoice_in_db.data) == NEW_RAW_ORDER
    reset_db(db_session)


def test_insert_invoice_that_exists_fail(invoice_x_supplier: Tuple[Invoice, Session]):
    invoice1, db_session = invoice_x_supplier
    with pytest.raises(DuplicateInvoiceException):
        invoice_service._insert_new_invoice_for_purchaser_x_supplier(
            raw_order = json.loads(invoice1.data),
            purchaser_id=invoice1.purchaser_id,
            supplier_id=invoice1.supplier_id,
            apr=.3,
            tenor_in_days=90,
            db=db_session
        )


def test_update_invoice_shipment_status(invoice_x_supplier):
    invoice1, db_session = invoice_x_supplier
    invoice_service.update_invoice_shipment_status(invoice1.id, "NEW_STATUS", db_session)
    after = invoice_service.get(db_session, invoice1.id)
    assert after.shipment_status == "NEW_STATUS"
    reset_db(db_session)


def test_update_invoice_with_payment_terms(invoice_x_supplier):
    invoice1, db_session = invoice_x_supplier
    _id = invoice1.id

    before = invoice_service.get(db_session, id=_id)
    assert json.loads(before.payment_details)['interest'] != 1000

    terms = invoice_to_terms(
        id=_id, order_id=invoice1.order_ref, amount=invoice1.value,
        apr=.16, tenor_in_days=90, loan_id="loanId1"
    )
    terms.interest = 1000
    invoice_service.update_invoice_with_loan_terms(before, terms, db_session)

    after = invoice_service.get(db_session, id=invoice1.id)
    assert json.loads(after.payment_details)['interest'] == 1000


def test_delete_invoice(invoice_x_supplier):
    invoice1, db_session = invoice_x_supplier
    _id = invoice1.id

    invoice_service.remove(db_session, id=_id)

    invoice = db_session.query(Invoice).filter(Invoice.id == _id).first()
    assert not invoice


def test_get_all_invoices(invoices):
    [invoice1, invoice2], db_session = invoices

    _invoices = invoice_service.get_all_invoices(db_session)

    ids_from_db = [i.id for i in _invoices]
    assert invoice1.id in ids_from_db
    assert invoice2.id in ids_from_db


def test_update_db(invoice_x_supplier):
    invoice1, db_session = invoice_x_supplier
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


def test_update_db_stores_update_timestamp_and_delivered_on(invoice_x_supplier):
    # save current status (same as what is on tusker-api)
    invoice, db_session = invoice_x_supplier
    assert invoice.shipment_status == "DELIVERED"

    # change status on db so that whatever is pulled from tusker will be new
    invoice_service.update_invoice_shipment_status(invoice.id, "somestatus", db_session)
    before = invoice_service.get_all_invoices(db_session)[0]
    last_updated = before.updated_on
    updated, errored = invoice_service.update_invoice_db(db_session)

    assert not errored

    after = invoice_service.get_all_invoices(db_session)[0]

    assert last_updated < after.updated_on

    assert after.delivered_on is not None


def test_update_invoices(invoice_x_supplier):
    invoice1, db_session = invoice_x_supplier
    assert invoice1.finance_status == FinanceStatus.INITIAL
    assert invoice1.shipment_status == "DELIVERED"

    # NOTE this does not expect to log the transaction to chain as our tests do not have a local algorand chain running
    invoice_service.update_invoice_payment_status(db_session, invoice1.id, FinanceStatus.REPAID, tx_id='tx1')
    invoice_service.update_invoice_shipment_status(invoice1.id, "IN_TRANSIT", db_session)

    assert invoice1.finance_status == FinanceStatus.REPAID
    assert invoice1.shipment_status == "IN_TRANSIT"


@pytest.mark.skip()
def test_multiple_invoice_updates():
    # see whether
    pass


@pytest.mark.skip()
def test_update_error_reporting():
    # see whether errors are reported correctly
    pass
 

