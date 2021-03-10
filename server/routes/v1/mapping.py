from fastapi import APIRouter, Body, HTTPException, Form, Depends
from pydantic import BaseModel
from starlette.status import (HTTP_400_BAD_REQUEST,
                              HTTP_412_PRECONDITION_FAILED,
                              HTTP_500_INTERNAL_SERVER_ERROR)
from typing import List, Dict
     
from humps import camelize
from utils.common import Mapping, MappingInput
from utils.constant import DISBURSAL_EMAIL
from utils.email import EmailClient, terms_to_email_body
from invoice.invoice import invoice_to_terms
from utils.security import check_jwt_token
from invoice.tusker_client import tusker_client
from db.utils import get_invoices

# ==================== Input Output Classes ==========================
# class UserStatusInput(BaseModel):
#     user_id: str


# class UserStatusResponse(BaseModel):
#     user_id: str
#     status: str


# class UserRegistrationInput(BaseModel):
#     name: str
#     should_succeed: bool
#     s3_file: str


# class RegistrationResponse(BaseModel):
#     flag: bool
#     status: str
#     user_id: str
#     received_files: List[str]


# ======================== ENDPOINTS ==================================
mapping_app = APIRouter()

# ======================= mock-rc-logic ===============================



@mapping_app.get("/", tags=["RC"])
def health():
    return {"OK"}


# def _get_mapping(mapping_request: MappingInput, role: str = Depends(check_jwt_token)):
@mapping_app.post("/mapping", response_model=Mapping, tags=["RC"])
def _get_mapping(mapping_request: MappingInput):
    # if role != "rc_backend":
        # raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Wrong permissions")
    # TODO
    # get lender balances from RC-api
    # call fill_loan
    return Mapping(allocations={inv: 1 for inv in mapping_request.investor_ids})
