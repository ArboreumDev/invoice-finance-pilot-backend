from typing import Dict, List, Optional, Tuple

from database import crud
from database.exceptions import (DuplicatePurchaserEntryException,
                                 PurchaserLimitException,
                                 UnknownPurchaserException)
from database.schemas.purchaser import PurchaserUpdate
from fastapi import APIRouter, Body, Depends, HTTPException
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,
                              HTTP_425_TOO_EARLY)
from utils.common import CamelModel, PurchaserInfo
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


@purchaser_app.get("/purchaser", response_model=List[PurchaserFrontendInfo], tags=["purchaser"])
def _get_purchasers(
    # user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db)
    ):
    purchasers = crud.purchaser.get_all(db)
    return [
        PurchaserFrontendInfo(
            id=p.purchaser_id,
            name=p.name,
            credit_limit=p.credit_limit,
            credit_used=crud.invoice.get_sum_of_live_invoices_from_purchaser(p.purchaser_id, db)
        )
        for p in purchasers
    ]


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
