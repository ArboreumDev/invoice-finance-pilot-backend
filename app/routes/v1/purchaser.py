from typing import Dict, List, Optional, Tuple

from database import crud
from database.exceptions import UnknownPurchaserException
from fastapi import APIRouter, Body, Depends, HTTPException
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST
from utils.common import CamelModel
from utils.security import check_jwt_token_role

purchaser_app = APIRouter()


class PurchaserUpdateInput(CamelModel):
    """ this is basically the class as SupplierCreate, only that it inherits from CamelModel """

    purchaser_id: str
    credit_limit: Optional[int]


class PurchaserFrontendInfo(CamelModel):
    id: str
    name: str
    credit_limit: int
    credit_used: int
    city: str = ""
    location_id: str = ""
    phone: str = ""


@purchaser_app.get("/purchaser", response_model=List[PurchaserFrontendInfo], tags=["purchaser"])
def _get_purchasers(
    # user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    purchasers = crud.purchaser.get_all(db)
    ret = []
    for p in purchasers:
        # TODO its stupid that those are stored on the whitelist entry
        whitelist_entry = crud.whitelist.get_from_purchaser_id(db, p.purchaser_id)
        ret.append(
            PurchaserFrontendInfo(
                id=p.purchaser_id,
                name=p.name,
                credit_limit=p.credit_limit,
                credit_used=crud.invoice.get_sum_of_live_invoices_from_purchaser(p.purchaser_id, db),
                phone=whitelist_entry.phone,
                city=whitelist_entry.city,
                location_id=whitelist_entry.location_id,
            )
        )
    return ret


@purchaser_app.post("/purchaser/update", response_model=Dict, tags=["purchaser"])
def _update_supplier_entry(
    update: PurchaserUpdateInput = Body(..., embed=True),
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    # auth-note: tusker & loanAdmin can change that field
    try:
        crud.purchaser.update_purchaser(db=db, update=update)

    except UnknownPurchaserException as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
