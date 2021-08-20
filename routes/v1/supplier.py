from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from database import crud
from database.exceptions import DuplicateSupplierEntryException
from database.schemas.supplier import SupplierCreate
from routes.dependencies import get_db
from utils.common import CamelModel, SupplierInfo
from utils.security import check_jwt_token_role

supplier_app = APIRouter()


class SupplierInput(CamelModel):
    """ this is basically the class as SupplierCreate, only that it inherits from CamelModel """

    supplier_id: str
    name: str
    creditline_size: int
    default_apr: float
    default_tenor_in_days: int


class SupplierUpdateInput(CamelModel):
    supplier_id: str
    creditline_size: Optional[int]
    apr: Optional[float]
    tenor_in_days: Optional[int]
    creditline_id: Optional[str]


@supplier_app.get("/supplier", response_model=List[SupplierInfo])
def _get_suppliers(user_info: Tuple[str, str] = Depends(check_jwt_token_role), db: Session = Depends(get_db)):
    suppliers = crud.supplier.get_all_suppliers(db)
    return [
        SupplierInfo(
            **{
                "name": s.name,
                "id": s.supplier_id,
                "creditline_size": s.creditline_size,
                "default_terms": {"apr": s.default_apr, "tenor_in_days": s.default_tenor_in_days, "creditline_size": 0},
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
        crud.supplier.create(db=db, obj_in=SupplierCreate(**input.dict()))


@supplier_app.post("/supplier/update", response_model=Dict, tags=["invoice"])
def _update_supplier_entry(
    update: SupplierUpdateInput = Body(..., embed=True),
    user_info: Tuple[str, str] = Depends(check_jwt_token_role),
    db: Session = Depends(get_db),
):
    try:
        crud.supplier.update(db, update=update)
    except DuplicateSupplierEntryException:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Supplier entry not found")
