import pytest
import copy
from database.invoice_service import InvoiceService, invoice_to_terms
from database.whitelist_service import WhitelistService
from database.exceptions import UnknownPurchaserException, WhitelistException
from utils.common import PurchaserInfo
from typing import Tuple
from database.test.fixtures import get_new_raw_order, OTHER_CUSTOMER_ID, OTHER_PURCHASER_ID

invoice_service = InvoiceService()
whitelist_service = WhitelistService()


def test_insert_whitelisted_invoice_success(whitelist_entry: Tuple[PurchaserInfo, str]):
    _p1, _supplier_id = whitelist_entry
    invoice_service.insert_new_invoice_from_raw_order(
        raw_order=get_new_raw_order(
            purchaser_name=_p1.name,
            purchaser_location_id=_p1.location_id,
            supplier_id=_supplier_id
        )
    )

def test_insert_whitelisted_fail_unknown_purchaser(whitelist_entry: Tuple[PurchaserInfo, str]):
    _p1, _supplier_id = whitelist_entry
    assert OTHER_PURCHASER_ID != _p1.id
    with pytest.raises(UnknownPurchaserException):
        invoice_service.insert_new_invoice_from_raw_order(
            raw_order=get_new_raw_order(
                purchaser_name=_p1.name,
                purchaser_location_id=OTHER_PURCHASER_ID,
                supplier_id=_supplier_id
            )
        )


def test_insert_whitelisted_fail_purchaser_not_whitelisted(whitelist_entry: Tuple[PurchaserInfo, str]):
    _p1, _supplier_id = whitelist_entry

    assert OTHER_CUSTOMER_ID != _supplier_id
    with pytest.raises(WhitelistException):
        invoice_service.insert_new_invoice_from_raw_order(
            raw_order=get_new_raw_order(
                purchaser_name=_p1.name,
                purchaser_location_id=_p1.location_id,
                supplier_id=OTHER_CUSTOMER_ID
            )
        )


