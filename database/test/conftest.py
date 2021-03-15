import pytest
from database.service import InvoiceService
from database.models import Invoice
from database.test.fixtures import RAW_ORDER
from invoice.tusker_client import tusker_client

invoice_service = InvoiceService()

@pytest.fixture(scope="function")
def invoice1():
    invoice_id = invoice_service.insert_new_invoice(RAW_ORDER)
    invoice = invoice_service.session.query(Invoice).filter(Invoice.id==invoice_id).first()
    yield invoice
    invoice_service.session.delete(invoice)
    invoice_service.session.commit()




