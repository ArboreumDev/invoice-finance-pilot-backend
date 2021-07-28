from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from database.exceptions import (DuplicateWhitelistEntryException,
                                 WhitelistException)
from database.models import Supplier
from database.whitelist_service import whitelist_service
from invoice.tusker_client import tusker_client
from utils.common import CamelModel, PurchaserInfo, SupplierInfo
from utils.security import check_jwt_token_role

# ===================== routes ==========================
whitelist_app = APIRouter()


class WhitelistInput(CamelModel):
    supplier_id: str
    purchaser: PurchaserInfo


class SupplierUpdate(CamelModel):
    supplier_id: str
    creditline_size: Optional[int]
    apr: Optional[float]
    tenor_in_days: Optional[int]


class WhitelistUpdateInput(SupplierUpdate):
    purchaser_id: str


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
def _update_whitelist_entry(
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
    except WhitelistException:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="whitelist entry not found")


@whitelist_app.post("/whitelist/search/{searchString}", response_model=Dict, tags=["invoice"])
def _search_purchaser(searchString: str, user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    try:
        return tusker_client.customer_to_receiver_info(search_string=searchString)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


# TODO properly do this
@whitelist_app.get("/supplier", response_model=List[SupplierInfo])
def _get_suppliers(user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    suppliers = whitelist_service.session.query(Supplier).all()
    return [
        SupplierInfo(
            **{
                "name": s.name,
                "id": s.supplier_id,
                "default_terms": {"apr": s.default_apr, "tenor_in_days": s.default_tenor_in_days,
                                  "creditline_size": s.creditline_size},
            }
        ).dict()
        for s in suppliers
    ]


@whitelist_app.post("/supplier/update", response_model=Dict)
def _update_supplier(
        update: SupplierUpdate = Body(..., embed=True), user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    s = whitelist_service.session.query(Supplier).filter_by(supplier_id=update.supplier_id).first()
    if not s:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="supplier already added")
    if update.apr:
        s.default_apr = update.apr
    if update.tenor_in_days:
        s.default_tenor_in_days = update.tenor_in_days
    if update.creditline_size:
        s.creditline_size = update.creditline_size
    whitelist_service.session.commit()


@whitelist_app.post("/supplier/new", response_model=Dict)
def _add_supplier(
        supplier: SupplierInfo = Body(..., embed=True), user_info: Tuple[str, str] = Depends(check_jwt_token_role)):
    exists = whitelist_service.session.query(Supplier).filter_by(supplier_id=supplier.id).first() is not None
    if not exists:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="supplier does not exist")
    s = Supplier(supplier_id=supplier.id,
                 name=supplier.name,
                 creditline_size=supplier.default_terms.creditline_size,
                 default_apr=supplier.default_terms.apr,
                 default_tenor_in_days=supplier.default_terms.tenor_in_days)
    whitelist_service.session.add(s)
    whitelist_service.session.commit()