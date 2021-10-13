from typing import Optional, Tuple

import pendulum
from database.crud.invoice_service import invoice as invoice_service
from fastapi import APIRouter, Body, Depends, HTTPException
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from utils.common import CamelModel
from utils.security import check_jwt_token_role
from algorand.algo_service import algo_service

# ===================== routes ==========================
admin_app = APIRouter()


class InvoiceUpdateInput(CamelModel):
    invoice_id: str
    new_status: Optional[str]
    new_value: Optional[str]
    loan_id: Optional[str]
    tx_id: Optional[str]
    disbursal_date: Optional[str]
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

    if update.signature_verification_result:
        invoice_service.update_invoice_payment_details(
            update.invoice_id, {"verification_result": update.signature_verification_result}, db
        )

    if update.new_status:
        if update.new_status == "FINANCED":
            if not update.loan_id:
                raise HTTPException(HTTP_400_BAD_REQUEST, "Missing value for loan_id")

            if not update.disbursal_date:
                raise HTTPException(HTTP_400_BAD_REQUEST, "Missing value for disbursal_date")

            try:
                as_timestamp = pendulum.parse(update.disbursal_date, strict=False, tz="Asia/Kolkata").int_timestamp
                if as_timestamp > pendulum.now().int_timestamp:
                    raise HTTPException(HTTP_400_BAD_REQUEST, "Disbursal date can not be from the future")

                invoice_service.update_invoice_payment_status(
                    db=db,
                    invoice_id=update.invoice_id,
                    new_status=update.new_status,
                    loan_id=update.loan_id,
                    tx_id=update.tx_id,
                    disbursal_time=as_timestamp,
                )
                return {"OK"}
            except pendulum.parsing.exceptions.ParserError:
                raise HTTPException(HTTP_400_BAD_REQUEST, "Invalid date format")
        else:
            invoice_service.update_invoice_payment_status(
                db=db,
                invoice_id=update.invoice_id,
                new_status=update.new_status,
                loan_id=update.loan_id,
                tx_id=update.tx_id,
            )
            return {"OK"}

@admin_app.post("/asset/new/{loan_id}")
def _create_new_asset_for_loan_id(
    loan_id: str,
    db: Session = Depends(get_db),
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
):
    _, role = user_info
    if role != "loanAdmin":
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing admin credentials")

    try: 
        algo_service.tokenize_loan(loan_id, db)
    except Exception as e:
        print(e)
        raise HTTPException(HTTP_400_BAD_REQUEST, str(e))



