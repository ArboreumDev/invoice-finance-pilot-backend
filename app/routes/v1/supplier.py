from typing import Dict, List, Optional, Tuple

from database import crud
from database.exceptions import (DuplicateSupplierEntryException,
                                 SupplierException)
from database.schemas.supplier import SupplierCreate
from database.schemas.whitelist import WhitelistUpdate
from fastapi import APIRouter, Body, Depends, HTTPException
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,
                              HTTP_425_TOO_EARLY)
from utils.common import CamelModel, SupplierInfo
from utils.constant import (ARBOREUM_DISBURSAL_EMAIL, DISBURSAL_EMAIL,
                            MAX_TUSKER_CREDIT)
from utils.email import EmailClient, new_supplier_to_email_body
from utils.security import check_jwt_token_role

supplier_app = APIRouter()


class SupplierInput(CamelModel):
    """ this is basically the class as SupplierCreate, only that it inherits from CamelModel """

    supplier_id: str
    name: str
    creditline_size: int
    default_apr: float
    default_tenor_in_days: int
    data: str


class SupplierUpdateInput(CamelModel):
    supplier_id: str
    creditline_id: Optional[str]
    creditline_size: Optional[int]
    apr: Optional[float]
    tenor_in_days: Optional[int]
    cascade: bool = True


@supplier_app.get("/supplier", response_model=List[SupplierInfo])
def _get_suppliers(user_info: Tuple[str, str] = Depends(check_jwt_token_role), db: Session = Depends(get_db)):
    suppliers = crud.supplier.get_all_suppliers(db)
    return [
        SupplierInfo(
            **{
                "name": s.name,
                "id": s.supplier_id,
                "creditline_size": s.creditline_size,
                "creditline_id": s.creditline_id,
                "default_terms": {"apr": s.default_apr, "tenor_in_days": s.default_tenor_in_days, "creditline_size": 0},
                "data": s.data,
            }
        ).dict()
        for s in suppliers
    ]


@supplier_app.post("/supplier/new", response_model=Dict, tags=["invoice"])
def _insert_new_supplier_entry(
    input: SupplierInput = Body(..., embed=True),
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    exists = crud.supplier.get(db, input.supplier_id) is not None
    if exists:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="supplier already exists")
    else:
        # check against total tusker-credit-limit
        available_credit = MAX_TUSKER_CREDIT - crud.supplier.get_total_extended_credit(db)
        print(MAX_TUSKER_CREDIT, crud.supplier.get_total_extended_credit(db))
        if available_credit < input.creditline_size:
            raise HTTPException(HTTP_400_BAD_REQUEST, detail=f"Max Credit exceeded: available {available_credit}")
        new_supplier = crud.supplier.create(db=db, obj_in=SupplierCreate(**input.dict()))
        try:
            ec = EmailClient()
            msg = new_supplier_to_email_body(new_supplier)
            print(msg)
            ec.send_email(
                body=msg, subject="New Supplier Register", targets=[DISBURSAL_EMAIL, ARBOREUM_DISBURSAL_EMAIL]
            )
        except Exception as e:
            print(e)
            # log error
            raise HTTPException(HTTP_425_TOO_EARLY, detail=f"Registered supplier but could not send email: {str(e)}")


@supplier_app.post("/supplier/update", response_model=Dict, tags=["invoice"])
def _update_supplier_entry(
    update: SupplierUpdateInput = Body(..., embed=True),
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    _, role = user_info
    if update.creditline_id and role != "loanAdmin":
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Unauthorized: Only the loanAdmin should change that field"
        )

    try:
        crud.supplier.update(db, update=update)
        if update.cascade and (update.tenor_in_days or update.apr):
            u = update.dict()
            if "creditline_size" in u:
                del u["creditline_size"]  # those need to be set manually
            crud.whitelist.update_from_supplier_terms(db, update.supplier_id, WhitelistUpdate(**u))

    except DuplicateSupplierEntryException:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Supplier entry not found")

    except SupplierException as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
