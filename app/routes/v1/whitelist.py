from typing import Dict, Optional, Tuple

from database.crud import whitelist as whitelist_service
from database.exceptions import (DuplicateWhitelistEntryException,
                                 WhitelistException)
from database.schemas.whitelist import WhitelistUpdate
from database.utils import remove_none_entries
from fastapi import APIRouter, Body, Depends, HTTPException
from invoice.tusker_client import tusker_client
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from utils.common import CamelModel, PurchaserInfo
from utils.security import check_jwt_token_role

# ===================== routes ==========================
whitelist_app = APIRouter()


class WhitelistInput(CamelModel):
    supplier_id: str
    purchaser: PurchaserInfo


class WhitelistUpdateInput(CamelModel):
    supplier_id: str
    purchaser_id: str
    creditline_size: Optional[int]
    apr: Optional[float]
    tenor_in_days: Optional[int]


@whitelist_app.post("/whitelist/new", response_model=Dict, tags=["invoice"])
def _insert_new_whitelist_entry(
    input: WhitelistInput = Body(..., embed=True),
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    try:
        # print('try adding ', input) # LOG
        whitelist_service.insert_whitelist_entry(
            db=db,
            supplier_id=input.supplier_id,
            purchaser=input.purchaser,
            creditline_size=input.purchaser.terms.creditline_size,
            apr=input.purchaser.terms.apr,
            tenor_in_days=input.purchaser.terms.tenor_in_days,
        )
    except DuplicateWhitelistEntryException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="receiver already whitelisted")


@whitelist_app.post("/whitelist/update", response_model=Dict, tags=["invoice"])
def _update_whitelist_entry(
    update: WhitelistUpdateInput = Body(..., embed=True),
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    # TODO  check if I can use different way to use Depends
    try:
        whitelist_service.update_whitelist_entry(  # **update)
            db=db,
            supplier_id=update.supplier_id,
            purchaser_id=update.purchaser_id,
            update=WhitelistUpdate(**remove_none_entries(update.dict())),
        )
    except DuplicateWhitelistEntryException:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="receiver already whitelisted")
    except WhitelistException:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="whitelist entry not found")


@whitelist_app.post("/whitelist/search/{searchString}", response_model=Dict, tags=["invoice"])
def _search_tusker_user(searchString: str, user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    try:
        return tusker_client.customer_to_receiver_info(search_string=searchString)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
