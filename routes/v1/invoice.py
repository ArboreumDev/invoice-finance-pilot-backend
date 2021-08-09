from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,
                              HTTP_500_INTERNAL_SERVER_ERROR)

from database.exceptions import (CreditLimitException,
                                 DuplicateInvoiceException,
                                 UnknownPurchaserException, WhitelistException)
from database.invoice_service import invoice_service
from database.models import Supplier
from database.whitelist_service import whitelist_service
from invoice.tusker_client import tusker_client
from invoice.utils import db_invoice_to_frontend_info, raw_order_to_invoice
from utils.common import CamelModel, CreditLineInfo, InvoiceFrontendInfo
from utils.security import check_jwt_token_role
from database.db import SessionLocal

# ===================== routes ==========================
invoice_app = APIRouter()


class OrderRequest(CamelModel):
    order_ids: List[str]


# # Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

@invoice_app.get("/")
def _health():
    return {"Ok"}


@invoice_app.get("/order/{order_reference_number}", response_model=InvoiceFrontendInfo, tags=["orders"])
def _get_order(order_reference_number: str, user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    """ read raw order data from tusker """
    username, role = user_info
    print(f"{username} with role {role} wants to know about order {order_reference_number}")
    raw_orders = tusker_client.track_orders([order_reference_number])
    # check against whitelist
    if raw_orders:
        raw_order = raw_orders[0]
        supplier_id = raw_order.get("cust").get("id")
        target_location_id = raw_order.get("rcvr").get("id")
        if not whitelist_service.location_is_whitelisted(supplier_id, target_location_id):
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Target not whitelisted for supplier")
        else:
            return raw_order_to_invoice(raw_order)
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Unknown order id: Order not found")


# @invoice_app.get("/order", response_model=List[Invoice], tags=["orders"])
# def _get_orders(input: OrderRequest):
#     """ read raw order data from tusker for multiple orders"""
#     # TODO implement caching layer to not hit Tusker API  too often
#     raw_orders = tusker_client.track_orders(input.order_ids)
#     return [raw_order_to_invoice(order) for order in raw_orders]


# @invoice_app.get("/invoice", response_model=List[InvoiceFrontendInfo], tags=["invoice"])
@invoice_app.get("/invoice", tags=["invoice"])
def _get_invoices_from_db():
    """
    return all invoices that we are currently tracking as they are in our db
    """
    # TODO filter by customer once we have more than one
    invoices = invoice_service.get_all_invoices()
    print("found", len(invoices))
    # print(invoices[0] if invoices)
    # return invoices
    return [db_invoice_to_frontend_info(inv) for inv in invoices]


@invoice_app.post("/invoice/update", response_model=Dict, tags=["invoice"])
def _update_invoice_db():
    """
    updating the invoices in our DB with the latest data from tusker
    then return them all
    """
    updated, error = invoice_service.update_invoice_db()
    # for order_id, new_status in updates:
    if error:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=error)
    return {"updated": updated, "error": error}


@invoice_app.post("/invoice/{order_reference_number}", response_model=Dict, tags=["invoice"])
def _add_new_invoice(order_reference_number: str):
    # get raw order
    orders = tusker_client.track_orders([order_reference_number])
    if not orders:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Unknown order id")
    raw_order = orders[0]

    try:
        invoice_service.check_credit_limit(raw_order)
        invoice_service.insert_new_invoice_from_raw_order(raw_order)

    except CreditLimitException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Not enough credit")
    except DuplicateInvoiceException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invoice already exists")
    except WhitelistException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Reciever not whitelisted")
    except UnknownPurchaserException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid recipient")
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown Failure, please inform us:" + str(e)
        )
    #  notify disbursal manager about the request
    # TODO

    # change status to awaiting_delivery
    # invoice_service.update_invoice_shipment_status(order_id, "AWAITING_DELIVERY")


@invoice_app.get("/credit", response_model=Dict[str, Dict[str, CreditLineInfo]])
def _get_creditSummary(user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    res = {"tusker": invoice_service.get_provider_summary(provider="tusker")}
    suppliers = whitelist_service.session.query(Supplier).all()
    for s in suppliers:
        res[s.supplier_id] = invoice_service.get_credit_line_info(supplier_id=s.supplier_id)
    return res
