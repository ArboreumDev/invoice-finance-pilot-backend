from typing import Optional

from airtable.airtable_service import AirtableService
# from database.exceptions import UnknownPurchaserException
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from routes.dependencies import get_air
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from database.exceptions import ( UnknownPhoneNumberException)


class AccountCallbackData(BaseModel):
    attempt: Optional[int]
    timestamp: Optional[str]
    callbackTxnId: Optional[str]
    originalCallbackTxnId: Optional[str]
    balance: Optional[int]
    accountNumber: str
    transactionMessage: Optional[str]
    type: Optional[str]
    transferType: Optional[str]
    transactionAmount: Optional[float]
    decentroTxnId: Optional[str]
    payeeAccountNumber: Optional[str]
    payeeAccountIfsc: Optional[str]
    providerCode: Optional[str]
    payeeVpa: Optional[str]
    payerAccountNumber: Optional[str]
    payerAccountIfsc: Optional[str]
    payerVpa: Optional[str]
    bankReferenceNumber: Optional[str]
    payerMobileNumber: Optional[str]


SAMPLEBODY = AccountCallbackData(
    **{
        "attempt": 1,
        "timestamp": "2020-09-16 23:23:23",
        "callbackTxnId": "CLBACKxx",
        "originalCallbackTxnId": "CLBACKxx",
        "accountNumber": "462515097596706652",
        "balance": 345,
        "transactionMessage": "message denoting the origination of balance update",
        "type": "credit",
        "transferType": "IMPS",
        "transactionAmount": 5.0,
        "decentroTxnId": "DCTRTXxx",
        "payeeAccountNumber": "ABC",
        "payeeAccountIfsc": "YESBXXXXXXXX",
        "providerCode": "YESB",
        "payeeVpa": "GHI",
        "payerAccountNumber": "JKL",
        "payerAccountIfsc": "MNO",
        "payerVpa": "PQR",
        "bankReferenceNumber": "STU",
        "payerMobileNumber": "1234567890",
        "payerName": "Payer Name",
    }
)


accounts_app = APIRouter()


@accounts_app.post("/update")
# def fetch_statement(update: AccountCallback)
def fetch_statement(update: AccountCallbackData, air: AirtableService = Depends(get_air)):
    try:
        # update = SAMPLEBODY
        # account_number = update.get("accountNumber", "")
        account_number = update.accountNumber
        if not account_number:
            raise HTTPException(HTTP_400_BAD_REQUEST, detail="missing key accountNumber with the input")
        return air.set_fetch_needed(account_number=account_number)
    except UnknownPhoneNumberException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
