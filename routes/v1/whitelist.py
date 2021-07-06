from typing import Dict

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST

from database.exceptions import DuplicateWhitelistEntryException
from database.whitelist_service import whitelist_service
from utils.common import PurchaserInfo

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
            tenor_in_days=input.tenor_in_days,
        )
    except DuplicateWhitelistEntryException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="receiver already whitelisted")
