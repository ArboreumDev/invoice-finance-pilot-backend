# %%
import pytest
from database.service import InvoiceService
from database.models import Invoice
from database.test.fixtures import NEW_RAW_ORDER
from database.db import metadata, engine, session
from invoice.tusker_client import code_to_order_status, tusker_client
import contextlib
import json
from utils.constant import MAX_CREDIT
from database.test.conftest import reset_db

invoice_service = InvoiceService()
# %%



# %%
# @pytest.mark.skip()
def test_reset_db():
    reset_db()
    invoice_service.insert_new_invoice(NEW_RAW_ORDER)
    reset_db()
    after = invoice_service.get_all_invoices()
    assert len(after) == 0


def test_insert_invoice(invoice1):
    before = invoice_service.get_all_invoices()

    invoice_id = invoice_service.insert_new_invoice(NEW_RAW_ORDER)

    after = invoice_service.get_all_invoices()

    # verify there is an extra invoice and its the one newly added
    assert len(after) == len(before) + 1
    assert invoice_id in [i.id for i in after]

    # assert properties are correctly mapped
    invoice_in_db = [i for i in after if i.id == invoice_id][0]
    assert invoice_in_db.value == NEW_RAW_ORDER.get("prc", {}).get("pr_act", 0)
    assert invoice_in_db.order_ref == NEW_RAW_ORDER.get('ref_no')
    assert invoice_in_db.shipment_status == "PLACED_AND_VALID"
    assert invoice_in_db.finance_status == "INITIAL"

    # check raw data is conserved
    assert json.loads(invoice_in_db.data) == NEW_RAW_ORDER
    # reset_db()

def test_update_invoice_status(invoice1):
    invoice_service.update_invoice_shipment_status(invoice1.id, "NEW_STATUS")
    assert invoice1.shipment_status == "NEW_STATUS"
    reset_db()


def test_delete_invoice(invoice1):
    _id = invoice1.id

    invoice_service.delete_invoice(_id)

    invoice = invoice_service.session.query(Invoice).filter(Invoice.id == _id).first()
    assert not invoice
    # reset_db()


# @pytest.mark.skip()
def test_get_all_invoices(invoices):
    [invoice1, invoice2] = invoices
    print(invoices)

    _invoices = invoice_service.get_all_invoices()

    ids_from_db = [i.id for i in _invoices]
    assert invoice1.id in ids_from_db
    assert invoice2.id in ids_from_db

def test_update_db(invoice1):
    # save current status (same as what is on tusker-api)
    tmp = invoice1.shipment_status
    # change status on db so that whatever is pulled from tusker will be new
    invoice1.shipment_status = "somestatus"

    updated, errored = invoice_service.update_invoice_db()

    assert not errored
    assert updated[0][0] == invoice1.id
    assert updated[0][1] == tmp

def test_free_credit(invoices):
    assert invoice_service.free_credit() == MAX_CREDIT

    in1 = invoices[0]
    in1.finance_status = "DISBURSED"
    invoice_service.update_invoice_payment_status(in1.id, "DISBURSED")
    # verify invoices with disbursed status are deducted from available credit

    assert invoice_service.free_credit() == MAX_CREDIT - in1.value


