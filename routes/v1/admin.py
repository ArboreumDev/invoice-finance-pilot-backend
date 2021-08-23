from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from database.crud import whitelist as whitelist_service
from database.crud.invoice_service import invoice as invoice_service
from database.exceptions import UnknownPurchaserException
from invoice.tusker_client import tusker_client
from routes.dependencies import get_db
from utils.security import check_jwt_token_role

# ===================== routes ==========================
admin_app = APIRouter()

# DESC: this is just a very fast hack to have an admin interface so that non-technical
# people can play around with it without having to use dev-tools like insomnia


@admin_app.post("/update/value/{invoiceId}/{value}")
def update_invoice_value(invoiceId: str, value: int, db: Session = Depends(get_db), user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    _, role = user_info
    if role != "loanAdmin":
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing admin credentials")
    invoice_service.update_invoice_value(invoiceId, int(value), db)
    return {"OK"}


@admin_app.post("/update/status/{invoiceId}/{new_status}")
def update_invoice_finance_status(
        invoiceId: str, new_status: str, loan_id: str = "", tx_id: str = "",
        db: Session = Depends(get_db),
        user_info: Tuple[str, str] = Depends(check_jwt_token_role)
    ):
    _, role = user_info
    if role != "loanAdmin":
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing admin credentials")
    if new_status == "FINANCED" and not loan_id:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Missing value for loan_id")
    invoice_service.update_invoice_payment_status(
        db=db, invoice_id=invoiceId, new_status=new_status, loan_id=loan_id, tx_id=tx_id
    )
    return {"OK"}

