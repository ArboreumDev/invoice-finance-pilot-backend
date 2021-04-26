import pytest
from database.service import InvoiceService
from database.db import engine
from database.models import Invoice, Base
from database.test.fixtures import RAW_ORDER, NEW_RAW_ORDER, get_new_raw_order
from invoice.tusker_client import tusker_client
from utils.constant import WHITELIST_DB, GURUGRUPA_CUSTOMER_ID
from database.whitelist_service import get_whitelist_info_for_customer


invoice_service = InvoiceService()


def reset_db():
    invoice_service.session.connection().execute("delete from invoice")
    invoice_service.session.commit()


@pytest.fixture(scope="function")
def invoice1():
    reset_db()
    invoice_id = invoice_service.insert_new_invoice(RAW_ORDER)
    invoice = invoice_service.session.query(Invoice).filter(Invoice.id==invoice_id).first()

    yield invoice

    reset_db()


# @pytest.fixture(scope="function")
# def invoice2():
#     reset_db()
#     invoice_id = invoice_service.insert_new_invoice(NEW_RAW_ORDER)
#     invoice = invoice_service.session.query(Invoice).filter(Invoice.id==invoice_id).first()
#     yield invoice
#     invoice_service.session.delete(invoice)
#     invoice_service.session.commit()



# @pytest.fixture(scope='function')
# def some_resource(request):
#     stuff_i_setup = ["I setup"]

#     def some_teardown():
#         stuff_i_setup[0] += " ... but now I'm torn down..."
#         print stuff_i_setup[0]
#     request.addfinalizer(some_teardown)

#     return stuff_i_setup[0]

@pytest.fixture(scope="function")
def invoices():
    """ insert two invoices from gurugrupa to their whitelisted receivers """
    whitelist_info = get_whitelist_info_for_customer(GURUGRUPA_CUSTOMER_ID)

    reset_db()
    invoice_service.insert_new_invoice(get_new_raw_order(receiver=whitelist_info[0].receiver_info))
    invoice_service.insert_new_invoice(get_new_raw_order(receiver=whitelist_info[1].receiver_info))
    invoices = invoice_service.session.query(Invoice).all()

    yield invoices

    reset_db()




