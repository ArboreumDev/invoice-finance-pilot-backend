from typing import Dict, List, Tuple

from database import crud
from database.crud.invoice_service import invoice_to_terms
from database.exceptions import (CreditLimitException,
                                 DuplicateInvoiceException,
                                 UnknownPurchaserException, WhitelistException)
from fastapi import APIRouter, Depends, HTTPException, Response
from invoice.tusker_client import tusker_client
from invoice.utils import db_invoice_to_frontend_info, raw_order_to_invoice
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED,
                              HTTP_404_NOT_FOUND,
                              HTTP_500_INTERNAL_SERVER_ERROR)
from utils.common import (CamelModel, CreditLineInfo, InvoiceFrontendInfo,
                          PaymentDetails)
from utils.logger import get_logger
from utils.security import check_jwt_token_role

# ===================== routes ==========================
invoice_app = APIRouter()
invoice_service = crud.invoice
whitelist_service = crud.whitelist


class OrderRequest(CamelModel):
    order_ids: List[str]


@invoice_app.get("/order/{order_reference_number}", response_model=InvoiceFrontendInfo, tags=["orders"])
def _get_order(
    order_reference_number: str,
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    """ read raw order data from tusker """
    username, role = user_info
    print(f"{username} with role {role} wants to know about order {order_reference_number}")
    raw_orders = tusker_client.track_orders([order_reference_number])
    # check against whitelist
    if raw_orders:
        raw_order = raw_orders[0]
        supplier_id = raw_order.get("cust").get("id")
        target_location_id = raw_order.get("rcvr").get("id")
        if not whitelist_service.location_is_whitelisted(db, supplier_id, target_location_id):
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Target not whitelisted for supplier")
        else:
            # get hypothetical terms
            invoice = raw_order_to_invoice(raw_order)
            supplier = crud.supplier.get(db, supplier_id)
            if supplier:
                terms = invoice_to_terms(
                    id=invoice.invoice_id,
                    order_id=invoice.order_id,
                    amount=invoice.value,
                    apr=supplier.default_apr,
                    tenor_in_days=supplier.default_tenor_in_days,
                )
                invoice.payment_details = PaymentDetails(
                    principal=terms.principal, interest=terms.interest, apr=terms.apr, tenor_in_days=terms.tenor_in_days
                )
            return invoice
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Unknown order id: Order not found")


# @invoice_app.get("/invoice", response_model=List[InvoiceFrontendInfo], tags=["invoice"])
@invoice_app.get("/invoice", tags=["invoice"])
def _get_invoices_from_db(db: Session = Depends(get_db)):
    """
    return all invoices that we are currently tracking as they are in our db
    """
    # TODO filter by customer once we have more than one
    invoices = invoice_service.get_all_invoices(db)
    print("found", len(invoices))
    return [
        db_invoice_to_frontend_info(inv=inv, purchaser=whitelist_service.get(db, inv.supplier_id, inv.purchaser_id))
        for inv in invoices
    ]


@invoice_app.post("/invoice/update", response_model=Dict, tags=["invoice"])
def _update_invoice_db(db: Session = Depends(get_db)):
    """
    updating the invoices in our DB with the latest data from tusker
    then return them all
    """
    updated, error = invoice_service.update_invoice_db(db)
    if error:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=error)
    return {"updated": updated, "error": error}


@invoice_app.post("/invoice/{order_reference_number}", response_model=Dict, tags=["invoice"])
def _add_new_invoice(order_reference_number: str, db: Session = Depends(get_db)):
    # get raw order
    orders = tusker_client.track_orders([order_reference_number])
    if not orders:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Unknown order id")
    raw_order = orders[0]

    try:
        invoice_service.check_credit_limit(raw_order, db)
        invoice_service.insert_new_invoice_from_raw_order(raw_order, db)

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
def _get_creditSummary(user_info: Tuple[str, str] = Depends(check_jwt_token_role), db: Session = Depends(get_db)):
    res = {"tusker": invoice_service.get_provider_summary(provider="tusker", db=db)}
    suppliers = crud.supplier.get_all_suppliers(db)
    for s in suppliers:
        res[s.supplier_id] = invoice_service.get_credit_line_info(supplier_id=s.supplier_id, db=db)
    return res


@invoice_app.post("/invoice/verification/{invoice_id}/{verified}", tags=["invoice"])
def _mark_invoice_verification_status(
    invoice_id: str,
    verified: bool,
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    username, role = user_info
    # if role != 'tusker':
    #     raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="only tusker should be setting this")

    logger = get_logger(__name__)
    logger.info(f"{username} with role {role} sets invoice verification status to {verified}")
    invoice_service.update_verification_status(db, invoice_id, verified)
    return {"status": "OK"}


@invoice_app.get("/invoice/image/{invoice_id}", response_class=Response)
def _get_invoice_image_from_tusker(
    invoice_id: str, db: Session = Depends(get_db), user_info: Tuple[str, str] = Depends(check_jwt_token_role)
):
    if user_info[1] != "loanAdmin":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")
    invoice = crud.invoice.get(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Unknown invoice id")

    # user order id of invoice to pull latest data from tusker
    raw_order = tusker_client.track_orders([invoice.order_ref])[0]
    documents = [d for d in raw_order.get("documents", []) if d.get("template_code", 0) == 1]
    if len(documents) == 0:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No documents attached")
    # image_link = documents[0].get("particulars", {}).get("doc_image", "")
    # if not image_link:
    #     raise HTTPException(status_code=HTTP_412_PRECONDITION_FAILED, detail="Empty doc_image link")

    # most test data wont have an image... for debugging purpose here is one that exists
    image_link = "doc_fcdf7709-0436-40ce-a77e-629bee25fee8.jpeg"
    if isinstance(image_link, str):
        res = tusker_client.get_invoice_image(image_link)
        return Response(content=res.content, status_code=200, media_type="image/png")

    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Invalid image link")
