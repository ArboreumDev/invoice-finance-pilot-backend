from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
from utils.common import FundAllocation, Invoice, Listing
from utils.security import check_jwt_token
from utils.tusker_client import tusker_client


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


@app_v1.get("/invoice", response_model=List[Invoice], tags=["invoice"])
def get_invoices():
    # TODO (later) check cache, if older than X hours, re-fetch from Tusker API and update DB with it / alternative use cron job 

    # UDIT # insert code that fetches all invoices from the DB and strips away what we dont want to have in the frontend

    return list(invoices.values())


@app_v1.post("/invoice", response_model=Invoice, tags=["invoice"])
def update_invoice(invoice: Invoice):
    invoices[invoice.id] = invoice
    return invoice


# response_model=Invoice, tags=["invoice"])
@app_v1.get("/mapping")
def get_mapping(listing: Listing, role: str = Depends(check_jwt_token)):
    if not role == "rc_admin" and not role == "admin":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Wrong permissions")
    # TODO
    # get lender mappings from RC-API
    # call fulfill module

    # return dummy value
    return FundAllocation(
        total_amount=listing.total_amount,
        lender_contributions={"l1": listing.total_amount / 2, "l2": listing.total_amount / 2},
    )


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
