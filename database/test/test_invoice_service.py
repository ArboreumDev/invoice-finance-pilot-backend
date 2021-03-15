# %%
import pytest
from database.service import InvoiceService
from database.models import Invoice
from database.test.fixtures import NEW_RAW_ORDER
from database.db import metadata, engine
from invoice.tusker_client import code_to_order_status, tusker_client
import contextlib

invoice_service = InvoiceService()
# %%

# @pytest.fixture(scope="session")
def reset_db():
    invoice_service.session.connection(Invoice.__table__.delete())

@pytest.mark.skip()
def test_insert_invoice():
    # invoice_id = invoice_service.insert_new_invoice(NEW_RAW_ORDER)
    # invoice = invoice_service.session.query(Invoice).filter(Invoice.id==invoice_id).first()
    # assert invoice.order_ref == NEW_RAW_ORDER.get('ref_no')
    # TODO verify price
    # verify shipping status is correctly translated
    # verify finance status is correctly translated
    # check raw data is conserved

    # clean up
    # invoice_service.delete_invoice(invoice.id)
    # assert invoice_service.session.query(Invoice).filter(Invoice.id==invoice_id).count() == 0
    pass

@pytest.mark.skip()
def test_update_invoice_status():
    pass

def test_delete_invoice(invoice1):
    _id = invoice1.id

    invoice_service.delete_invoice(_id)

    invoice = invoice_service.session.query(Invoice).filter(Invoice.id == _id).first()
    assert not invoice

@pytest.mark.skip()
def test_get_all_invoices():
    pass

def test_update_db(invoice1):
    new_status = invoice1.shipment_status
    invoice1.shipment_status = "o"
    print(invoice1.shipment_status)
    updated, errored = invoice_service.update_invoice_db()
    assert not errored
    assert updated[0][0] == invoice1.id
    assert updated[0][1] == new_status



