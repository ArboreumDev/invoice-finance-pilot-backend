from typing import Dict, Callable
from db.models import Invoice, InvoiceTable
from db.database import session
from invoice.tusker_client import  tusker_client, code_to_order_status
from datetime import  datetime


def update_invoice_db():
    # for all existing invoice (TODO where status is not final)
    res = session.query(Invoice).all()
    invoices = {i.source_id: i for i in res}
    # fetch invoice data from TuskerAPI...
    # tusker_client(ids)
    raw_latest_orders = tusker_client.get_latest_invoices(list(invoices.keys()))
    #...and update DB with em
    for order in raw_latest_orders[:1]:
        print('updating', order.get('id'))
        update_invoice(order, invoices[order['id']])
    

def insert_invoice_from_order(raw_order: Dict):
    # if invoice is there -> update invoice (relevant fields)
    print('raw', raw_order)
    # else insert new one
    temp = {}
    temp['cost'] = raw_order.get("prc", {}).get("pr_f", 0)
    temp['delivery_date'] = str(raw_order.get("eta", {}))
    temp["finance_status"] = "NONE"
    temp["shipment_status"] = code_to_order_status(raw_order["status"])
    temp["source_id"] = raw_order.get("id")
    temp["created_on"] = datetime.now()
    # TODO insert raw_order as pickledump
    InvoiceTable.insert().values(**temp).execute()

    return True

def update_invoice(raw_order: Dict, invoice: Invoice):
    ret = ""
    # check if status_changed
    new_shipment_status = raw_order.get("status")
    if code_to_order_status[new_shipment_status] != code_to_order_status[int(invoice.shipment_status)]:
        # print(new_shipment_status, type(new_shipment_status))
        print(invoice.shipment_status, type(invoice))
        print('new shipment status: ', code_to_order_status[new_shipment_status])
        # update relevant fields
        invoice.shipment_status = new_shipment_status
        ret = invoice.id, code_to_order_status[new_shipment_status]

    invoice.updated_on = datetime.now()
    session.commit()
    return ret

# filtering 
# invoices = session.query(Invoice).filter(Invoice.c.finance_status!="PENDING").all()
# invoices = query.execute()

update_invoice_db()

# TODO
# - get all invoices for a given list of ids
# - move db-definition into the repo
# - learn how to deploy it
# - figure out how to write to the DB DONE
# - turn enums into strings
# new_shipment_status = code_to_order_status(raw_order.get("status"))
# if new_shipment_status != code_to_order_status(invoice.shipment_status):
#     print('new shipment status', new_shipment_status)
#     # update relevant fields
#     invoice.status = order_to_shipping_status(new_shipment_status)
#     # return new status if there was a transition
#     ret = new_shipment_status

