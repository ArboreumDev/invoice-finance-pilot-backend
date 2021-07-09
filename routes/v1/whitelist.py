from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST

from database.exceptions import DuplicateWhitelistEntryException
from database.whitelist_service import whitelist_service
from invoice.tusker_client import tusker_client
from utils.common import CamelModel, PurchaserInfo
from utils.security import check_jwt_token_role

# ===================== routes ==========================
whitelist_app = APIRouter()


class WhitelistInput(CamelModel):
    supplier_id: str
    purchaser: PurchaserInfo


class WhitelistUpdateInput(BaseModel):
    supplier_id: str
    purchaser_id: str
    creditline_size: Optional[int]
    apr: Optional[float]
    tenor_in_days: Optional[int]


# class WhitelistInput(CamelModel):
#     input: WhitelistInput2


@whitelist_app.post("/whitelist/new", response_model=Dict, tags=["invoice"])
def _insert_new_whitelist_entry(
    input: WhitelistInput = Body(..., embed=True), user_info: Tuple[str, str] = Depends(check_jwt_token_role)
):
    try:
        # print('try adding ', input) # LOG
        whitelist_service.insert_whitelist_entry(
            supplier_id=input.supplier_id,
            purchaser=input.purchaser,
            creditline_size=input.purchaser.terms.creditline_size,
            apr=input.purchaser.terms.apr,
            tenor_in_days=input.purchaser.terms.tenor_in_days,
        )
    except DuplicateWhitelistEntryException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="receiver already whitelisted")


@whitelist_app.post("/whitelist/update", response_model=Dict, tags=["invoice"])
def _update_new_whitelist_entry(
    update: WhitelistUpdateInput = Body(..., embed=True), user_info: Tuple[str, str] = Depends(check_jwt_token_role)
):
    # TODO  check if I can use different way to use Depends
    print("sf", update)
    try:
        whitelist_service.update_whitelist_entry(  # **update)
            supplier_id=update.supplier_id,
            purchaser_id=update.purchaser_id,
            creditline_size=update.creditline_size,
            apr=update.apr,
            tenor_in_days=update.tenor_in_days,
        )
    except DuplicateWhitelistEntryException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="receiver already whitelisted")


@whitelist_app.post("/whitelist/search/{searchString}", response_model=Dict, tags=["invoice"])
def _search_purchaser(searchString: str, user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    try:
        return tusker_client.customer_to_receiver_info(search_string=searchString)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
