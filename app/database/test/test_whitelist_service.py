from database import crud
from database.schemas import whitelist
import pytest
from typing import Tuple

from database.db import Session

from database.crud import whitelist as whitelist_service
from utils.common import PurchaserInfo
from database.test.conftest import db_session
from database.utils import reset_db
from database.test.fixtures import CUSTOMER_ID, p1, OTHER_CUSTOMER_ID, OTHER_PURCHASER_ID, OTHER_LOCATION_ID
from database.exceptions import DuplicateWhitelistEntryException, InsufficientCreditException


def test_insert_whitelist_entry(supplier_entry):
    supplier, db_session = supplier_entry
    whitelisted = whitelist_service.get_whitelisted_locations_for_supplier(db_session, CUSTOMER_ID)

    extended_credit_before = crud.supplier.get_extended_creditline(db_session, CUSTOMER_ID)

    assert len(whitelisted) == 0
    whitelist_service.insert_whitelist_entry(
        db_session,
        supplier_id=CUSTOMER_ID,
        purchaser=p1,
        creditline_size=50000,
        apr=0.1,
        tenor_in_days=90
    )

    whitelisted = whitelist_service.get_whitelisted_locations_for_supplier(db_session, CUSTOMER_ID)
    assert len(whitelisted) == 1

    extended_credit_after = crud.supplier.get_extended_creditline(db_session, CUSTOMER_ID)
    assert extended_credit_after == extended_credit_before + 50000

def test_insert_whitelist_entry_failure_credit_limit(supplier_entry):
    supplier, db_session = supplier_entry

    with pytest.raises(InsufficientCreditException):
        whitelist_service.insert_whitelist_entry(
            db_session,
            supplier_id=CUSTOMER_ID,
            purchaser=p1,
            creditline_size=supplier.creditline_size + 1,
            apr=0.1,
            tenor_in_days=90
        )



def test_insert_duplicate_whitelist_entry_fails(whitelist_entry: Tuple[PurchaserInfo, str, Session]):
    _p1, _customer_id, db = whitelist_entry
    with pytest.raises(DuplicateWhitelistEntryException):
        whitelist_service.insert_whitelist_entry(
            db,
            supplier_id=_customer_id,
            purchaser=_p1,
            creditline_size=50000,
            apr=0.1,
            tenor_in_days=90
        )

def test_whitelist_okay(whitelist_entry: Tuple[PurchaserInfo, str, Session]):
    _p1, _supplier_id, db = whitelist_entry
    assert whitelist_service.purchaser_is_whitelisted(db, _supplier_id, _p1.id)
    assert whitelist_service.location_is_whitelisted(db, _supplier_id, _p1.location_id)


def test_whitelist_failure(whitelist_entry: Tuple[PurchaserInfo, str, Session]):
    _p1, _supplier_id, db = whitelist_entry

    # verify with existing Purchaser/location
    assert not whitelist_service.purchaser_is_whitelisted(db, _supplier_id, OTHER_PURCHASER_ID)
    assert not whitelist_service.location_is_whitelisted(db, _supplier_id, OTHER_LOCATION_ID)

    # # verify with non existing Supplier
    assert not whitelist_service.purchaser_is_whitelisted(db, OTHER_CUSTOMER_ID, _p1.id)
    assert not whitelist_service.location_is_whitelisted(db, OTHER_CUSTOMER_ID, _p1.location_id)
    #     assert unknown_order_receiver not in whitelist_service.get_whitelisted_purchaser_ids(test_customer)
    #     assert not invoice_service.is_whitelisted(order, username="gurugrupa")
