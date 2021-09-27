import datetime as dt
from typing import Tuple

from database.crud import whitelist as whitelist_service
from database.crud.invoice_service import invoice as invoice_service
from database.exceptions import UnknownPurchaserException
from fastapi import APIRouter, Depends, HTTPException
from invoice.tusker_client import tusker_client
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import (HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND,
                              HTTP_500_INTERNAL_SERVER_ERROR)
from utils.security import check_jwt_token_role

# ===================== routes ==========================
test_app = APIRouter()


@test_app.patch("/update/shipment/{invoiceId}")
def mark_as_delivered(
    invoiceId: str, db: Session = Depends(get_db), user_info: Tuple[str, str] = Depends(check_jwt_token_role)
):
    if user_info[1] != "loanAdmin":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)
    # try:
    # res = tusker_client.mark_test_order_as(invoiceId, "DELIVERED")
    invoice = invoice_service.get(db, invoiceId)
    update = {"shipment_status": "DELIVERED"}
    invoice_service.update_and_log(db, invoice, update)
    order = tusker_client.track_orders([invoice.order_ref])[0]
    order['s_updt'] = dt.datetime.utcnow().timestamp()
    invoice_service.handle_update(db, invoice, "DELIVERED", order)


#     return {"OK"}

# except Exception as e:
#     print("error trying to mark invoice as delivered")
#     raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))


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
