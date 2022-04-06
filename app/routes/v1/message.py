from database.exceptions import (
    UnknownPhoneNumberException, NoDocumentsException, DuplicatePhoneNumberException, UserNotKYCedException
)
from typing import Dict, Optional, List
from utils.common import CamelModel
from pydantic import BaseModel
# from database.exceptions import UnknownPurchaserException
from fastapi import APIRouter, Body, Depends, HTTPException
from routes.dependencies import get_db, get_air
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from airtable.airtable_service import AirtableService


message_app = APIRouter()

class MessageCallbackData(BaseModel):
    srcAddr: str
    channel: str
    externalId: str
    cause: str
    errorCode: str
    destAddr: str
    eventType: str
    eventTs: int

SAMPLE_MESSAGE_DELIVERY = MessageCallbackData(**{
    "srcAddr": "TESTSM",
    "channel": "WHATSAPP",
    "externalId": "4611485671516594245-230140146681310845",
    "cause": "SUCCESS",
    "errorCode": "000",
    "destAddr": "918095997461",
    "eventType": "DELIVERED",
    "eventTs": 918095997461
})

SAMPLE_DELIVERY_DATA = [SAMPLE_MESSAGE_DELIVERY]


# def record_answer(update: List[MessageCallbackData], air: AirtableService = Depends(get_air)):
@message_app.post("/delivery")
def record_answer(data = Body(...), air: AirtableService = Depends(get_air)):
# def record_answer(data: List[MessageCallbackData], air: AirtableService = Depends(get_air)):
    # update = SAMPLEBODY
    print('data', data)
    # phone_number = update.phone_number
    # return air.set_lead_response(phone_number, update.answer)
    return {'status': 'success'}


class InboundCallbackData(BaseModel):
    waNumber: str
    mobile: str
    name: str
    text: str
    type: str
    timestamp: str

InboundCallbackData (**{
    "waNumber": "919999999999",
    "mobile": "919999999999",
    "name": "Test Name",
    "text": "Hello Sign me Up",
    "type": "text",
    "timestamp": "1623446483000"
})


@message_app.post("/inbound")
def record_inbound_message(data = Body(...), air: AirtableService = Depends(get_air)):
    print('data', data)
    return {'status': 'success'}


