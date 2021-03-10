from fastapi import APIRouter, Body, HTTPException, Form, Depends
from pydantic import BaseModel
from starlette.status import (HTTP_400_BAD_REQUEST,
                              HTTP_412_PRECONDITION_FAILED,
                              HTTP_500_INTERNAL_SERVER_ERROR)
from typing import List, Dict
     
from humps import camelize
from utils.common import Mapping, MappingInput
from utils.constant import DISBURSAL_EMAIL
from utils.fullfill_loan import fulfill
from utils.email import EmailClient, terms_to_email_body
from invoice.invoice import invoice_to_terms
from utils.security import check_jwt_token_role
from invoice.tusker_client import tusker_client
from db.utils import get_invoices
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from utils.rupeecircle_client import rc_client

class Item(BaseModel):
    id: str
    value: str


class Message(BaseModel):
    message: str


app = FastAPI()


# @app.get("/items/{item_id}", response_model=Item, responses={404: {"model": Message}})
# async def read_item(item_id: str):

# ======================== ENDPOINTS ==================================
mapping_app = APIRouter()


@mapping_app.get("/", tags=["RC"])
def health():
    return {"OK"}


# def _get_mapping(mapping_request: MappingInput, role: str = Depends(check_jwt_token)):
@mapping_app.post(
    "/mapping",
    response_model=Mapping, 
    responses={HTTP_400_BAD_REQUEST: {"model": Message, "description": "Invalid Funds"}}, 
    tags=["RC"]
)
# def _get_mapping(mapping_request: MappingInput):
def _get_mapping(mapping_request: MappingInput, role: str = Depends(check_jwt_token_role)):
    if role != "rc":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=f"Wrong permissions, role {role} not authorized")
    # TODO
    # get lender balances from RC-api
    lender_balances = rc_client.get_investor_balances(investor_ids=mapping_request.investor_ids)
    print(lender_balances)
    try:
        lender_contributions, _ = fulfill(mapping_request.loan_amount, lender_balances)
    except AssertionError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
        print(e)
    # call fill_loan
    return Mapping(allocations=lender_contributions)
