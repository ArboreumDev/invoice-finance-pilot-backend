import pytest
import math
import copy
from database import crud
from sqlalchemy.orm import Session
from database.crud.invoice_service import InvoiceService
from database.crud.whitelist_service import WhitelistService

invoice_service: InvoiceService = crud.invoice
whitelist_service: WhitelistService = crud.whitelist


def test_credit_line_breakdown(whitelisted_invoices):
    invoices, db = whitelisted_invoices
    in1 = invoices[0]
    supplier_id = in1.supplier_id
    whitelist_ids = whitelist_service.get_whitelisted_purchaser_ids(db, supplier_id)

    before = copy.deepcopy(invoice_service.get_credit_line_info(supplier_id, db))

    invoice_service.update_invoice_payment_status(
        db, in1.id, "FINANCED", loan_id="l1", tx_id="tx1", disbursal_time=1632497776
    )

    # verify invoices with disbursed status are deducted from available credit
    after =  invoice_service.get_credit_line_info(supplier_id, db)

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


def test_credit_line_breakdown_invalid_customer_id(db_session: Session):
    assert invoice_service.get_credit_line_info("deadbeef", db_session) == {}


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

