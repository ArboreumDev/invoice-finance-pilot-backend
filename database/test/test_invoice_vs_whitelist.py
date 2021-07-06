import pytest
import copy
from database.invoice_service import InvoiceService, invoice_to_terms
from database.whitelist_service import WhitelistService

invoice_service = InvoiceService()
whitelist_service = WhitelistService()


@pytest.mark.skip()
def test_insert_whitelisted_success():
    invoice_service.insert_new_invoice_from_raw_order(
        raw_order={}
    )

@pytest.mark.skip()
def test_insert_whitelisted_fail_unknown_purchaser():
    with pytest.raises(AssertionError):
        invoice_service.insert_new_invoice_from_raw_order(
            raw_order={}
        )

@pytest.mark.skip()
def test_insert_whitelisted_fail_purchaser_not_whitelisted():
    with pytest.raises(AssertionError):
        invoice_service.insert_new_invoice_from_raw_order(
            raw_order={}
        )

@pytest.mark.skip()
def test_insert_new_invoice_exceeds_credit_line_failure():
    pass

