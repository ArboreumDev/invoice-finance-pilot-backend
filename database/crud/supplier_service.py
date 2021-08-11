from os import name
from typing import Dict, List
from sqlalchemy.orm import Session
from database.db import session
from database.models import Supplier
from database.crud.base import CRUDBase
from database.schemas import SupplierCreate, SupplierUpdate


class SupplierService(CRUDBase[Supplier, SupplierCreate, SupplierUpdate]):
    def get(self, db: Session, supplier_id: str):
        return db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()

    def get_all_suppliers(self, db: Session):
        return db.query(Supplier).all()

    def remove(self, db: Session, supplier_id: str):
        obj = self.get(db, supplier_id)
        db.delete(obj)
        db.commit()
 
supplier = SupplierService(Supplier)