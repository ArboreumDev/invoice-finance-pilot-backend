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
from utils.security import jwt_token_role
from invoice.tusker_client import tusker_client
from db.utils import get_invoices

# ======================== ENDPOINTS ==================================
mapping_app = APIRouter()


@mapping_app.get("/", tags=["RC"])
def health():
    return {"OK"}


# def _get_mapping(mapping_request: MappingInput, role: str = Depends(check_jwt_token)):
@mapping_app.post("/mapping", response_model=Mapping, tags=["RC"])
# def _get_mapping(mapping_request: MappingInput):
def _get_mapping(mapping_request: MappingInput, role: str = Depends(jwt_token_role)):
    if role != "rc":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=f"Wrong permissions, role {role} not authorized}")
    # TODO
    # get lender balances from RC-api
    # call fill_loan
    return Mapping(allocations={inv: 1 for inv in mapping_request.investor_ids})
