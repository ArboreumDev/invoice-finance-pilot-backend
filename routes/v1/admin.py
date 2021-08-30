from typing import Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from database.crud.invoice_service import invoice as invoice_service
from routes.dependencies import get_db
from utils.common import CamelModel
from utils.security import check_jwt_token_role

# ===================== routes ==========================
admin_app = APIRouter()


class InvoiceUpdateInput(CamelModel):
    invoice_id: str
    new_status: Optional[str]
    new_value: Optional[str]
    loan_id: Optional[str]
    tx_id: Optional[str]
    signature_verification_result: Optional[str]


@admin_app.post("/update")
def update_invoice_finance_status(
    update: InvoiceUpdateInput = Body(..., embed=True),
    db: Session = Depends(get_db),
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
):
    _, role = user_info
    if role != "loanAdmin":
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing admin credentials")

    if update.new_value:
        invoice_service.update_invoice_value(update.invoice_id, update.new_value, db)

    if update.verification_result:
        invoice_service.update_invoice_payment_details(
            update.invoice_id,
            {"verification_result": update.signature_verification_result},
            db
        )

    if update.new_status:
        if update.new_status == "FINANCED" and not update.loan_id:
            raise HTTPException(HTTP_400_BAD_REQUEST, "Missing value for loan_id")
        invoice_service.update_invoice_payment_status(
            db=db,
            invoice_id=update.invoice_id,
            new_status=update.new_status,
            loan_id=update.loan_id,
            tx_id=update.tx_id,
        )
    return {"OK"}
