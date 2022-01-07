from database.utils import remove_none_entries
from routes.v1.purchaser import PurchaserUpdateInput
from database.exceptions import UnknownPurchaserException, DuplicatePurchaserEntryException
from os import name
from typing import Dict, List
from sqlalchemy.orm import Session
from database.db import session
from database.models import Purchaser
from database.crud.base import CRUDBase
from database.schemas import PurchaserCreate, PurchaserUpdate


class PurchaserService(CRUDBase[Purchaser, PurchaserCreate, PurchaserUpdate]):
    def get(self, db: Session, purchaser_id: str):
        return db.query(Purchaser).filter(Purchaser.purchaser_id == purchaser_id).first()

    def get_all(self, db: Session):
        return db.query(Purchaser).all()

    def remove(self, db: Session, purchaser_id: str):
        obj = self.get(db, purchaser_id)
        db.delete(obj)
        db.commit()

    def insert_new_purchaser(self, db: Session, new_purchaser: PurchaserCreate):
        exists = db.query(Purchaser).filter_by(purchaser_id = new_purchaser.purchaser_id).first() is not None
        if exists:
            self._logger.error( f"Duplicate Purchaser Error: purchaser: {new_purchaser.purchaser_id}")
            raise DuplicatePurchaserEntryException(f"Entry purchaser already exists")
        return self.create(db, obj_in=new_purchaser)

    def remove_if_there(self, db: Session, purchaser_id: str):
        if self.get(db, purchaser_id):
            self.remove(db, purchaser_id)
    
    def update_purchaser( self, db: Session, update: PurchaserUpdateInput):
        purchaser_entry = self.get(db, purchaser_id=update.purchaser_id)

        if not purchaser_entry:
            self._logger.error(f"Update target not found: purchaser_id: {update.purchaser_id}")
            raise UnknownPurchaserException("Purchaser entry doesnt exist")

        return super().update(
            db=db,
            db_obj=purchaser_entry,
            obj_in=PurchaserUpdate(**remove_none_entries(update.dict()))
        )

 
purchaser = PurchaserService(Purchaser)
