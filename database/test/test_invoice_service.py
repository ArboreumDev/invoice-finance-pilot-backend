# %%
import pytest
import copy
from database.service import InvoiceService, invoice_to_terms
from database.models import Invoice
from database.test.fixtures import NEW_RAW_ORDER, RAW_ORDER
from database.db import metadata, engine, session
from invoice.tusker_client import code_to_order_status, tusker_client
import contextlib
import json
from utils.constant import MAX_CREDIT, USER_DB, WHITELIST_DB, RECEIVER_ID1, GURUGRUPA_CUSTOMER_ID
from database.test.conftest import reset_db
import datetime as dt

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
    assert invoice_in_db.receiver_id == NEW_RAW_ORDER.get('rcvr').get('id')

    # check raw data is conserved
    assert json.loads(invoice_in_db.data) == NEW_RAW_ORDER
    reset_db()

@pytest.mark.skip()
def test_insert_invoice_that_exists():
    pass

def test_update_invoice_status(invoice1):
    invoice_service.update_invoice_shipment_status(invoice1.id, "NEW_STATUS")
    assert invoice1.shipment_status == "NEW_STATUS"
    reset_db()


def test_update_invoice_with_payment_terms(invoice1):
    terms = invoice_to_terms(invoice1.id, invoice1.value, dt.datetime.now())
    terms.interest = 1000
    invoice_service.update_invoice_with_loan_terms(invoice1, terms)

    assert json.loads(invoice1.payment_details)['interest'] == 1000
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


def test_update_invoices(invoice1):
    assert invoice1.finance_status == "INITIAL"
    assert invoice1.shipment_status == "DELIVERED"

    invoice_service.update_invoice_payment_status(invoice1.id, "PAID")
    invoice_service.update_invoice_shipment_status(invoice1.id, "IN_TRANSIT")

    assert invoice1.finance_status == "PAID"
    assert invoice1.shipment_status == "IN_TRANSIT"

    # invoice_service.update_invoice_payment_status

def test_whitelist_okay():
    test_customer = USER_DB.get("test").get('customer_id')
    whitelisted_receivers = list(WHITELIST_DB.get(test_customer).keys())
    order_receiver = NEW_RAW_ORDER.get('rcvr').get('id')

    assert order_receiver in whitelisted_receivers
    assert invoice_service.is_whitelisted(NEW_RAW_ORDER, username="test")

def test_whitelist_failure():
    test_customer = USER_DB.get("test").get('customer_id')
    whitelisted_receivers = list(WHITELIST_DB.get(test_customer).keys())

    #set order receiver to something not in whitelist
    order = copy.deepcopy(RAW_ORDER)
    order_receiver = "0xdeadbeef"
    order['rcvr']['id'] = order_receiver

    assert order_receiver not in whitelisted_receivers
    assert not invoice_service.is_whitelisted(order, username="test")



@pytest.mark.skip()
def test_multiple_invoice_updates():
    # see whether
    pass


@pytest.mark.skip()
def test_update_error_reporting():
    # see whether errors are reported correctly
    pass
 

def test_credit_line_breakdown(invoices):
    gurugrupa_receiver1 = list(WHITELIST_DB[GURUGRUPA_CUSTOMER_ID].keys())[0]
    gurugrupa_receiver2 = list(WHITELIST_DB[GURUGRUPA_CUSTOMER_ID].keys())[1]
    before = copy.deepcopy(invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID))

    in1 = invoices[0]
    invoice_service.update_invoice_payment_status(in1.id, "FINANCED")

    # verify invoices with disbursed status are deducted from available credit
    after =  invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID)
    assert in1.receiver_id == gurugrupa_receiver1
    assert after[gurugrupa_receiver1].used  == before[gurugrupa_receiver1].used + in1.value
    assert after[gurugrupa_receiver2].available == before[gurugrupa_receiver2].available

    # verify consistency
    c = after[gurugrupa_receiver2]
    c2 = before[gurugrupa_receiver2]
    assert c.available + c.used == c.total and c2.available + c2.used == c2.total

    # do the same for the DISBURSAL_REQUESTED status => iniital & disbursed are currently both shwon as requested
    # in2 = invoices[1]
    # invoice_service.update_invoice_payment_status(in2.id, "DISBURSAL_REQUESTED")
    # after = invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID)
    # assert after[gurugrupa_receiver1].used == before[gurugrupa_receiver1].used + in1.value + in2.value

def test_credit_line_breakdown_invalid_customer_id():
    assert invoice_service.get_credit_line_info("deadbeef") == {}