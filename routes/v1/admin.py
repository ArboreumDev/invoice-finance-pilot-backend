from typing import Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from database.crud import whitelist as whitelist_service
from database.crud.invoice_service import invoice as invoice_service
from database.exceptions import UnknownPurchaserException
from invoice.tusker_client import tusker_client
from routes.dependencies import get_db
from utils.security import check_jwt_token_role
from utils.common import CamelModel

# ===================== routes ==========================
admin_app = APIRouter()

# DESC: this is just a very fast hack to have an admin interface so that non-technical
# people can play around with it without having to use dev-tools like insomnia
class InvoiceUpdateInput(CamelModel):
    invoice_id: str
    new_status: Optional[str]
    new_value: Optional[str]
    loan_id: Optional[str]
    tx_id: Optional[str]


@admin_app.post("/update")
def update_invoice_finance_status(
        update: InvoiceUpdateInput = Body(..., embed=True),
        db: Session = Depends(get_db),
        user_info: Tuple[str, str] = Depends(check_jwt_token_role)
    ):
    _, role = user_info
    if role != "loanAdmin":
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing admin credentials")

    print('in', update)
    if update.new_value:
        invoice_service.update_invoice_value(update.invoice_id, update.new_value, db)

    if update.new_status:
        if update.new_status == "FINANCED" and not update.loan_id:
            raise HTTPException(HTTP_400_BAD_REQUEST, "Missing value for loan_id")
        invoice_service.update_invoice_payment_status(
            db=db, invoice_id=update.invoice_id, new_status=update.new_status, loan_id=update.loan_id, tx_id=update.tx_id
        )
    return {"OK"}

