from database.service import invoice_service
from database.test.conftest import reset_db
from invoice.tusker_client import tusker_client


def test_update_db():
    reset_db()
    # create a new order on tusker API
    inv_id, order_id, _ = tusker_client.create_test_order()
    raw_order = tusker_client.track_orders([order_id])[0]

    # insert it into DB
    inv_id = invoice_service.insert_new_invoice(raw_order)
    assert invoice_service.get_all_invoices()[0].id == inv_id  # < should be tested in invoice_service unit tests

    # update order on tusker side
    tusker_client.mark_test_order_as(inv_id, "IN_TRANSIT")

    # verify invoice gets updated with the status
    updated, _ = invoice_service.update_invoice_db()
    assert updated[0][0] == inv_id and updated[0][1] == "IN_TRANSIT"
    assert invoice_service.get_all_invoices()[0].shipment_status == "IN_TRANSIT"

    reset_db()
