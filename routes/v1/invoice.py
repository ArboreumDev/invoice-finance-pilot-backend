from typing import List

from fastapi import APIRouter, HTTPException
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,
                              HTTP_500_INTERNAL_SERVER_ERROR)

from database.service import invoice_service
from invoice.tusker_client import tusker_client
from utils.common import CamelModel, Invoice, InvoiceFrontendInfo
from utils.invoice import raw_order_to_invoice

# ===================== routes ==========================
invoice_app = APIRouter()

# PLAN
# /invoice  - Get - fetches all, Update - updates all, Delete - deletes all
# /invoice/<id>  - Get getches with that index, and so on


class OrderRequest(CamelModel):
    order_ids: List[str]


@invoice_app.get("/order/{order_reference_number}", response_model=Invoice, tags=["orders"])
def _get_order(order_reference_number: str):
    """ read raw order data from tusker """
    raw_orders = tusker_client.track_orders([order_reference_number])
    if raw_orders:
        return raw_order_to_invoice(raw_orders[0])
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Unknown order id")


@invoice_app.get("/order", response_model=List[Invoice], tags=["orders"])
def _get_orders(input: OrderRequest):
    """ read raw order data from tusker for multiple orders"""
    # TODO implement caching layer to not hit Tusker API  too often
    raw_orders = tusker_client.track_orders(input.order_ids)
    return [raw_order_to_invoice(order) for order in raw_orders]


@invoice_app.get("/invoice", response_model=List[InvoiceFrontendInfo], tags=["invoice"])
def _get_invoices_from_db():
    """
    return all invoices that we are currently tracking as they are in our db
    """
    invoices = invoice_service.get_all_invoices()
    return [InvoiceFrontendInfo(**inv.dict()) for inv in invoices]


@invoice_app.post("/invoice/update", response_model=List[Invoice], tags=["invoice"])
def _update_invoice_db():
    """
    updating the invoices in our DB with the latest data from tusker
    then return them all
    """
    invoice_service.update_invoice_db()
    error = ""
    if error:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=error)
    return {"OK"}


@invoice_app.post("/invoice/{order_reference_number}", response_model=Invoice, tags=["invoice"])
def add_new_invoice(order_reference_number: str):
    # get raw order
    raw_order = tusker_client.track_orders([order_reference_number])
    if not raw_order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Unknown order id")

    result, msg = invoice_service.final_checks(raw_order)
    if not result:
        if "credit" in msg:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Not enough credit")
        elif "whitelist" in msg:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid recipient")
        elif "status" in msg:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid order status")
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Unknown Failure, please inform us")

    #  create a new entry in DB for the order with status INITIAL
    order_id = invoice_service.insert_new_invoice(raw_order)

    #  notify disbursal manager about the request
    # TODO

    # change status to awaiting_delivery
    invoice_service.update_invoice_status(order_id, "AWAITING_DELIVERY")
    return {"Ok": "AWAITING_DELIVERY"}


# deprecated
# @invoice_app.post("/fund", tags=["invoice"])
# def fund_invoice(input: BaseInvoice, str=Depends(check_jwt_token)):
# ========== BASIC CHECKS ==================
# # get invoiceInfo
# if input.id not in invoices:
#     raise HTTPException(HTTP_404_NOT_FOUND, "unknown invoice id")
# invoice = invoices[input.id]
# if invoice.status != FinanceStatus.NONE:
#     raise HTTPException(HTTP_400_BAD_REQUEST, "Invoice not ready to be financed")
# # TODO verify that invoice has been uploaded

# # ========== change status of invoice in DB ==================
# invoice.status = FinanceStatus.FINANCED
# return {"status": "Request has been sent"}


# OPEN ?
# /repayment endoint
#  - ??? get banking info reference id to put on repayment?
# filterLogic:
# takes invoices and filters them (for starters, just return all of them)
