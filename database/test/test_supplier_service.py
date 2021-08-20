from routes.v1.supplier import SupplierUpdateInput
from database.schemas.supplier import SupplierCreate
from database.test.conftest import db_session, reset_db
import pytest
from typing import Tuple
import copy
from database import crud
from database.crud.invoice_service import invoice_to_terms
from database.crud import whitelist as whitelist_service
from utils.common import PurchaserInfo
from database.exceptions import SupplierException
from database.db import SessionLocal

db = SessionLocal()

def test_get_suppliers(supplier_entry):
    _, db_session = supplier_entry
    assert len(crud.supplier.get_all_suppliers(db_session)) == 1

def test_add_supplier(supplier_entry):
    _, db_session = supplier_entry

    before = len(crud.supplier.get_all_suppliers(db_session))

    crud.supplier.create(db, obj_in=SupplierCreate(
        supplier_id='supplier2',name='name',default_apr=0.42, default_tenor_in_days=42, creditline_size=42000, data="moreInfo"
    ))

    assert len(crud.supplier.get_all_suppliers(db_session)) == before + 1

    s = crud.supplier.get(db, supplier_id='supplier2')
    assert s.default_apr == 0.42
    assert s.default_tenor_in_days == 42
    assert s.creditline_size == 42000

    reset_db()


def test_update_supplier(supplier_entry):
    supplier, db_session = supplier_entry

    crud.supplier.update(
        db, 
        update=SupplierUpdateInput(
            supplier_id=supplier.supplier_id,
            creditline_size=41000,
            apr=.41,
            tenor_in_days=41
        )
    )

    s = crud.supplier.get(db, supplier.supplier_id)
    assert s.default_apr == 0.41
    assert s.default_tenor_in_days == 41
    assert s.creditline_size == 41000





