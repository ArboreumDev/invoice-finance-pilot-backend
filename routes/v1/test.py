from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from database.crud import whitelist as whitelist_service
from database.crud.invoice_service import invoice as invoice_service
from database.exceptions import UnknownPurchaserException
from invoice.tusker_client import tusker_client
from routes.dependencies import get_db
from utils.security import check_jwt_token_role

# ===================== routes ==========================
test_app = APIRouter()

# DESC: this is just a very fast hack to have an admin interface so that non-technical
# people can play around with it without having to use dev-tools like insomnia


@test_app.post("/update/value/{invoiceId}/{value}")
def update_invoice_value(invoiceId: str, value: int, db: Session = Depends(get_db)):
    print(invoiceId, value)
    invoice_service.update_invoice_value(invoiceId, int(value), db)
    return {"OK"}


@test_app.post("/update/status/{invoiceId}/{new_status}/{loan_id}")
def update_invoice_finance_status(invoiceId: str, new_status: str, loan_id: str = "", db: Session = Depends(get_db)):
    if new_status == "FINANCED" and not loan_id:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Missing value for loan_id")
    invoice_service.update_invoice_payment_status(invoiceId, new_status, loan_id, db)
    return {"OK"}


@test_app.post("/update/shipment/{invoiceId}/{new_status}")
def update_invoice_delivery_status(invoiceId: str, new_status: str, db: Session = Depends(get_db)):
    invoice_service.update_invoice_shipment_status(invoiceId, new_status, db)
    return {"OK"}


@test_app.patch("/update/shipment/{invoiceId}")
def mark_as_delivered(invoiceId: str):
    print("got as id", invoiceId)
    try:
        res = tusker_client.mark_test_order_as(invoiceId, "DELIVERED")
        if res:
            return {"OK"}

    except Exception as e:
        print("error trying to mark invoice as delivered")
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@test_app.post("/new/order/{supplier_id}/{purchaser_id}/{value}")
def create_new_test_order(
    supplier_id: str,
    purchaser_id: str,
    value: float,
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    username, _ = user_info
    try:
        target_id = whitelist_service.purchaser_id_to_location(db, purchaser_id)
        res = tusker_client.create_test_order(
            # TODO
            supplier_id=supplier_id,
            location_id=target_id,
            value=value,
        )
        invoice_id, ref_no, _ = res
        return {"status": "OK", "invoiceId": invoice_id, "orderRef": ref_no}
    except UnknownPurchaserException:
        raise HTTPException(HTTP_404_NOT_FOUND, f"couldnt find location id for purchaser id {purchaser_id}")
    except Exception as e:
        print(e)
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))
