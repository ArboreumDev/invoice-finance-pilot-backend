import pytest
import math
import copy
from database.invoice_service import InvoiceService, invoice_to_terms
from database.whitelist_service import WhitelistService
from database.test.conftest import reset_db
from database.models import Invoice
import datetime as dt


invoice_service = InvoiceService(Invoice)
whitelist_service = WhitelistService()


def test_credit_line_breakdown(whitelisted_invoices):
    in1 = whitelisted_invoices[0]
    supplier_id = in1.supplier_id
    whitelist_ids = whitelist_service.get_whitelisted_purchaser_ids(supplier_id)

    before = copy.deepcopy(invoice_service.get_credit_line_info(supplier_id))

    invoice_service.update_invoice_payment_status(in1.id, "FINANCED")

    # verify invoices with disbursed status are deducted from available credit
    after =  invoice_service.get_credit_line_info(supplier_id)

    assert after[in1.purchaser_id].used  == before[in1.purchaser_id].used + in1.value

    # verify second credit line is unaffected
    other_purchaser = whitelist_ids[1 if whitelist_ids[0] == in1.purchaser_id else 0]
    assert after[other_purchaser].available == before[other_purchaser].available

    # # verify consistency
    c = after[in1.purchaser_id]
    c2 = before[in1.purchaser_id]
    assert math.isclose(c.available + c.used + c.requested, c.total)
    assert math.isclose(c2.available + c2.used + c2.requested, c2.total)

    # do the same for the DISBURSAL_REQUESTED status => iniital & disbursed are currently both shwon as requested
    # in2 = invoices[1]
    # invoice_service.update_invoice_payment_status(in2.id, "DISBURSAL_REQUESTED")
    # after = invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID)
    # assert after[gurugrupa_receiver1].used == before[gurugrupa_receiver1].used + in1.value + in2.value

def test_credit_line_breakdown_invalid_customer_id():
    assert invoice_service.get_credit_line_info("deadbeef") == {}


@pytest.mark.skip()
def test_credit_line_summary(whitelisted_invoices):
    supplier_id = whitelisted_invoices[0].supplier_id

    # as all invoices are from one customer, they should match the invividual breakdown
    customer = invoice_service.get_credit_line_info(supplier_id)
    # TODO refactor the user db
    # summary = invoice_service.get_provider_summary("tusker")

    # assert sum(c.used for c in customer.values())== summary['gurugrupa'].used
    # assert sum(c.total for c in customer.values())== summary['gurugrupa'].total
    # assert sum(c.requested for c in customer.values())== summary['gurugrupa'].requested
    # assert sum(c.available for c in customer.values())== summary['gurugrupa'].available
    # assert sum(c.invoices for c in customer.values())== summary['gurugrupa'].invoices

@pytest.mark.skip()
def test_insert_new_invoice_exceeds_credit_line_failure():
    pass

