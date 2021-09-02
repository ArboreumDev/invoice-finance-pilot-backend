from database.utils import remove_none_entries
from routes.v1.supplier import SupplierUpdateInput
from database.exceptions import SupplierException, UnknownSupplierException
from os import name
from typing import Dict, List
from sqlalchemy.orm import Session
from database.db import session
from database.models import Supplier, Invoice, Whitelist
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
    
    def remove_if_there(self, db: Session, supplier_id: str):
        if self.get(db, supplier_id):
            self.remove(db, supplier_id)
    
    def get_used_creditline(self, db: Session, supplier_id: str):
        current_whitelist = db.query(Whitelist).filter(Whitelist.supplier_id == supplier_id).all()
        return sum(w.creditline_size for w in current_whitelist)

    def update( self, db: Session, update: SupplierUpdateInput):
        supplier_entry = self.get(db, supplier_id=update.supplier_id)

        if not supplier_entry:
            self._logger.error(f"Update target not found: supplier_id: {update.supplier_id}")
            raise UnknownSupplierException("Supplier entry doesnt exist")

        # only allow updating creditline_id if there are no live or requested invoices for that supplier
        if supplier_entry.creditline_id and update.creditline_id:
            live_invoices = db.query(Invoice).filter(
                Invoice.supplier_id == supplier_entry.supplier_id
            ).filter(
                Invoice.finance_status in ["FINANCED", "DISBURSAL_REQUESTED"]
            ).all()
            print('live',live_invoices, len(live_invoices))
            if len(live_invoices) > 0:
                raise SupplierException(
                    "Invalid Update: Supplier has live invoices and there this should not be changed. \
                    Contact your admin if you think otherwise"
                )

        return super().update(
            db=db,
            db_obj=supplier_entry,
            obj_in=SupplierUpdate(
                **remove_none_entries(update.dict()),
                default_apr=update.apr,
                default_tenor_in_days=update.tenor_in_days
            )
        )

 
supplier = SupplierService(Supplier)
