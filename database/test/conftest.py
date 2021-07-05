import pytest
from database.service import InvoiceService
from database.db import engine
from database.models import Invoice, Base
from database.test.fixtures import RAW_ORDER, NEW_RAW_ORDER, get_new_raw_order
from invoice.tusker_client import tusker_client
from utils.constant import GURUGRUPA_CUSTOMER_ID
from database.whitelist_service import whitelist_service


invoice_service = InvoiceService()


def reset_db(deleteWhitelist = False):
    invoice_service.session.connection().execute("delete from invoice")
    if deleteWhitelist:
        invoice_service.session.connection().execute("delete from whitelist")
    invoice_service.session.commit()


@pytest.fixture(scope="function")
def invoice1():
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




