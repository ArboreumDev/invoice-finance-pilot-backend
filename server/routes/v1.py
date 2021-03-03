from fastapi import FastAPI, Body, Header, File, APIRouter
from typing import List
from utils.common import Invoice

# FIXTURES to use instead of DB for now
def init_invoices():
    _invoices = [
        {"id": 1, "amount": 1000, "destination": "Ramesh", "shipping_status": "AWAITING_SHIPMENT"},
        {"id": 2, "amount": 1000, "destination": "Ajit", "shipping_status": "AWAITING_SHIPMENT"},
        {"id": 3, "amount": 1000, "destination": "Pavan", "shipping_status": "SHIPPING"},
    ]

    return {invoice["id"]: Invoice(**invoice) for invoice in _invoices}

invoices = init_invoices()

# ===================== routes ==========================
app_v1 = APIRouter()

# PLAN
# /invoice  - Get - fetches all, Update - updates all, Delete - deletes all
# /invoice/<id>  - Get getches with that index, and so on

@app_v1.get("/invoice", response_model=List[Invoice])
def get_invoices():
    # TODO check cache, if older than X hours, re-fetch from Tusker API and update DB with it
    return list(invoices.values())


@app_v1.post("/invoice", response_model=Invoice)
def update_invoice(invoice: Invoice):
    invoices[invoice.id] = invoice
    return invoice


# TODO
# add /finance endoint
#  - verify if invoice is ok for financing
#    - (e.g. if it has a bill of sufficient quality attached to it?)
#    - if amount does not exceed current credit line
#  - send email to RC
#  - change status of invoice

# TODO
# add /repayment endoint
#  - ??? get banking info reference id to put on repayment?


# Add filterLogic:
# takes invoices and filters them (for starters, just return all of them)

# @app.post("/email", response_model=TODO}
# should send an email to rupeeCircle



