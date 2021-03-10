import datetime as dt
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import (HTTP_401_UNAUTHORIZED,
                              HTTP_500_INTERNAL_SERVER_ERROR,
                              HTTP_404_NOT_FOUND,
                              HTTP_400_BAD_REQUEST,
                              )
from utils.common import BaseInvoice, FundAllocation, Invoice, Listing, FinanceStatus
from utils.constant import DISBURSAL_EMAIL
from utils.email import EmailClient, terms_to_email_body
from invoice.invoice import invoice_to_terms
from utils.security import check_jwt_token
from invoice.tusker_client import tusker_client
from db.utils import get_invoices


# FIXTURES to use instead of DB for now
def init_invoices():
    _invoices = [
        {"id": "id1", "amount": 1000, "destination": "Ramesh", "shipping_status": "AWAITING_SHIPMENT"},
        {"id": "id2", "amount": 1000, "destination": "Ajit", "shipping_status": "AWAITING_SHIPMENT"},
        {"id": "id3", "amount": 1000, "destination": "Pavan", "shipping_status": "SHIPPING"},
    ]

    return {invoice["id"]: Invoice(**invoice) for invoice in _invoices}


invoices = init_invoices()

# ===================== routes ==========================
app_v1 = APIRouter()

# PLAN
# /invoice  - Get - fetches all, Update - updates all, Delete - deletes all
# /invoice/<id>  - Get getches with that index, and so on


@app_v1.get("/invoice", response_model=List[Invoice], tags=["invoice"])
def _get_invoices():
    # TODO (later) check cache, if older than X hours,
    # re-fetch from Tusker API and update DB with it / alternative use cron job

    # UDIT # insert code that fetches all invoices from the DB and strips away what we dont want to have in the frontend

    # print(get_invoices())
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


@app_v1.post("/fund", tags=["invoice"])
def fund_invoice(input: BaseInvoice, str=Depends(check_jwt_token)):
    # ========== BASIC CHECKS ==================
    # get invoiceInfo
    if input.id not in invoices:
        raise HTTPException(HTTP_404_NOT_FOUND, "unknown invoice id")
    invoice = invoices[input.id]
    if invoice.status != FinanceStatus.NONE:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Invoice not ready to be financed")
    # TODO verify that invoice has been uploaded

    # ============== get loan terms ==========
    # calculate repayment info
    # TODO get actual invoice start date & amount here using input.id
    start_date = dt.datetime.utcnow()
    amount = 1000
    msg = terms_to_email_body(invoice_to_terms(input.id, amount, start_date))

    # ================= send email to Tusker with FundRequest
    try:
        ec = EmailClient()
        ec.send_email(body=msg, subject="Arboreum Disbursal Request", targets=[DISBURSAL_EMAIL])
    except Exception as e:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    print("email sent")
    # TODO send confirmation mail to GP

    # ========== change status of invoice in DB ==================
    invoice.status = FinanceStatus.FINANCED
    return {"status": "Request has been sent"}


# TODO
# add /repayment endoint
#  - ??? get banking info reference id to put on repayment?


# Add filterLogic:
# takes invoices and filters them (for starters, just return all of them)

# @app.post("/email", response_model=TODO}
# should send an email to rupeeCircle
