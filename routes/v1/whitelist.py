from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Body
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,
                              HTTP_500_INTERNAL_SERVER_ERROR)

from database.exceptions import (CreditLimitException,
                                 DuplicateInvoiceException,
                                 UnknownPurchaserException, WhitelistException,
                                 DuplicateWhitelistEntryException)
from database.invoice_service import invoice_service
from database.whitelist_service import whitelist_service
from invoice.tusker_client import tusker_client
from invoice.utils import db_invoice_to_frontend_info, raw_order_to_invoice
from utils.common import CamelModel, CreditLineInfo, InvoiceFrontendInfo, PurchaserInfo
from utils.constant import USER_DB
from utils.security import check_jwt_token_role
from pydantic import BaseModel

# ===================== routes ==========================
whitelist_app = APIRouter()


class WhitelistInput(BaseModel):
    supplier_id: str
    purchaser: PurchaserInfo
    creditline_size: int
    apr: float
    tenor_in_days: int

# class WhitelistInput(CamelModel):
#     input: WhitelistInput2

@whitelist_app.post("/whitelist/new", response_model=Dict, tags=["invoice"])
def _insert_new_whitelist_entry(input: WhitelistInput = Body(..., embed=True)):
    try: 
        whitelist_service.insert_whitelist_entry(
            supplier_id=input.supplier_id,
            purchaser=input.purchaser,
            creditline_size=input.creditline_size,
            apr=input.apr,
            tenor_in_days=input.tenor_in_days
        )
    except DuplicateWhitelistEntryException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="receiver already whitelisted")
 