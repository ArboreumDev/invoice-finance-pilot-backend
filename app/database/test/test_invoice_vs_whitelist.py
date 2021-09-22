import pytest
from database import crud
from database.exceptions import UnknownPurchaserException, WhitelistException
from utils.common import PurchaserInfo
from typing import Tuple
from database.test.fixtures import get_new_raw_order, OTHER_CUSTOMER_ID, OTHER_PURCHASER_ID
from sqlalchemy.orm import Session

invoice_service = crud.invoice


def test_insert_whitelisted_invoice_success(whitelist_entry: Tuple[PurchaserInfo, str, Session]):
    _p1, _supplier_id, db = whitelist_entry
    before = len(invoice_service.get_all_invoices(db))
    invoice_service.insert_new_invoice_from_raw_order(
        raw_order=get_new_raw_order(
            purchaser_name=_p1.name,
            purchaser_location_id=_p1.location_id,
            supplier_id=_supplier_id
        ),
        db=db
    )
    after = len(invoice_service.get_all_invoices(db))
    assert after == before + 1


def test_insert_whitelisted_fail_unknown_purchaser(whitelist_entry: Tuple[PurchaserInfo, str, Session]):
    _p1, _supplier_id, db = whitelist_entry
    assert OTHER_PURCHASER_ID != _p1.id
    with pytest.raises(UnknownPurchaserException):
        invoice_service.insert_new_invoice_from_raw_order(
            raw_order=get_new_raw_order(
                purchaser_name=_p1.name,
                purchaser_location_id=OTHER_PURCHASER_ID,
                supplier_id=_supplier_id
            ),
            db=db
        )


def test_insert_whitelisted_fail_purchaser_not_whitelisted(whitelist_entry: Tuple[PurchaserInfo, str, Session]):
    _p1, _supplier_id, db = whitelist_entry

    assert OTHER_CUSTOMER_ID != _supplier_id
    with pytest.raises(WhitelistException):
        invoice_service.insert_new_invoice_from_raw_order(
            raw_order=get_new_raw_order(
                purchaser_name=_p1.name,
                purchaser_location_id=_p1.location_id,
                supplier_id=OTHER_CUSTOMER_ID
            ),
            db=db
        )


