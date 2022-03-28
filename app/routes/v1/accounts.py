from database.exceptions import (
    UnknownPhoneNumberException, NoDocumentsException, DuplicatePhoneNumberException, UserNotKYCedException
)
from pydantic import BaseModel
# from database.exceptions import UnknownPurchaserException
from fastapi import APIRouter, Body, Depends, HTTPException
from routes.dependencies import get_db, get_air
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from airtable.airtable_service import AirtableService

class AccountCallback(BaseModel):
    attempt: int 
    timestamp: str
    callbackTxnId: str 
    originalCallbackTxnId: str 
    accountNumber: str 
    balance: int 
    transactionMessage: str
    type: str 
    transferType: str 
    transactionAmount: float 
    decentroTxnId: str 
    payeeAccountNumber: str 
    payeeAccountIfsc: str 
    providerCode: str 
    payeeVpa: str 
    payerAccountNumber: str 
    payerAccountIfsc: str 
    payerVpa: str 
    bankReferenceNumber: str 
    payerMobileNumber: str 
	

SAMPLEBODY = AccountCallback(**{
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
	"payerName": "Payer Name"
})


accounts_app = APIRouter()

@accounts_app.post("/update")
# def fetch_statement(update: AccountCallback)
def fetch_statement(air: AirtableService = Depends(get_air)):
    update = SAMPLEBODY
    return air.set_fetch_needed(account_number= update.accountNumber)


