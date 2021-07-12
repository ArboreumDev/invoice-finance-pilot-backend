import pytest
from database.invoice_service import InvoiceService
from database.db import engine
from database.models import Invoice, Base
from database.test.fixtures import OTHER_CUSTOMER_ID, RAW_ORDER, NEW_RAW_ORDER, get_new_raw_order, p2, p1
from invoice.tusker_client import tusker_client
from utils.constant import GURUGRUPA_CUSTOMER_ID
from database.whitelist_service import whitelist_service
from typing import Tuple
import copy
from database.whitelist_service import WhitelistService
from utils.common import PurchaserInfo

invoice_service = InvoiceService()


def reset_db(deleteWhitelist = False):
    invoice_service.session.connection().execute("delete from invoice")
    invoice_service.session.connection().execute("delete from users")
    invoice_service.session.connection().execute("delete from supplier")
    if deleteWhitelist:
        invoice_service.session.connection().execute("delete from whitelist")
    invoice_service.session.commit()


@pytest.fixture(scope="function")
def invoice1():
    """ will only insert into invoices table, there will be no connected entries"""
    reset_db()
    invoice_id = invoice_service._insert_new_invoice_for_purchaser_x_supplier(RAW_ORDER, "testP", "testS")
    invoice = invoice_service.session.query(Invoice).filter(Invoice.id==invoice_id).first()

    yield invoice

    reset_db()


@pytest.fixture(scope="function")
def invoices():

    reset_db()
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(
        get_new_raw_order(purchaser_name='p1', purchaser_location_id='l1'), 'p1', 's1'
    )
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(
        get_new_raw_order(purchaser_name='p2', purchaser_location_id='l2'), 'p1', 's1'
    )
    invoices = invoice_service.session.query(Invoice).all()

    yield invoices

    reset_db()

@pytest.fixture(scope="function")
def whitelisted_invoices():
    reset_db(deleteWhitelist=True)

    # create two whitelist entry for supplier
    _supplier_id=CUSTOMER_ID
    _purchaser=p1

    whitelist_service.insert_whitelist_entry(
        supplier_id=_supplier_id,
        purchaser=_purchaser,
        creditline_size=50000,
        apr=0.1,
        tenor_in_days=90
    )

    whitelist_service.insert_whitelist_entry(
        supplier_id=_supplier_id,
        purchaser=p2,
        creditline_size=40000,
        apr=0.1,
        tenor_in_days=90
    )

    # create two invoices for the first entry
    invoice_service.insert_new_invoice_from_raw_order(
        get_new_raw_order(
            purchaser_name=_purchaser.name,
            purchaser_location_id=_purchaser.location_id,
            supplier_id=_supplier_id
        )
    )
    invoice_service.insert_new_invoice_from_raw_order(
        get_new_raw_order(
            purchaser_name=_purchaser.name,
            purchaser_location_id=_purchaser.location_id,
            supplier_id=_supplier_id
        )
    )
    invoices = invoice_service.session.query(Invoice).all()

    yield invoices

    reset_db(deleteWhitelist=True)

 


CUSTOMER_ID = "0001e776-c372-4ec5-8fa4-f30ab74ca631"
p1 = PurchaserInfo(id='aa8b8369-be51-49a3-8419-3d1eb8c4146c', name='Mahantesh Medical', phone='+91-9449642927', city='Kundagol', location_id='e0f2c12d-9371-4863-a39a-0037cd6c711b')
@pytest.fixture(scope="function")
def whitelist_entry() -> Tuple[PurchaserInfo, str]:
    reset_db(deleteWhitelist=True)
    whitelist_service.insert_whitelist_entry(
        supplier_id=CUSTOMER_ID,
        purchaser=p1,
        creditline_size=50000,
        apr=0.1,
        tenor_in_days=90
    )

    yield p1, CUSTOMER_ID

    reset_db(deleteWhitelist=True)


