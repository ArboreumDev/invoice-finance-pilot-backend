from os import name
from utils.common import PurchaserInfo, WhiteListEntry, Terms
from typing import Dict, List
from database.exceptions import (DuplicateWhitelistEntryException, UnknownPurchaserException, WhitelistException)

from sqlalchemy.orm import Session
from database import crud
from database.models import Whitelist
from database.crud.base import CRUDBase
from database.schemas import WhitelistCreate, WhitelistUpdate

def whitelist_entry_to_receiverInfo(entry: Whitelist):
    return PurchaserInfo(
        id=entry.purchaser_id,
        name=entry.name,
        phone=entry.phone,
        city=entry.city,
        location_id=entry.location_id,
        terms=Terms(
            apr=entry.apr,
            tenor_in_days=entry.tenor_in_days,
            creditline_size=entry.creditline_size
        )
    )


class WhitelistService(CRUDBase[Whitelist, WhitelistCreate, WhitelistUpdate]):
    def get(self, db: Session, supplier_id: str, purchaser_id: str) -> Whitelist:
        return db.query(Whitelist).filter(Whitelist.supplier_id == supplier_id, Whitelist.purchaser_id == purchaser_id).first()

    def get_whitelisted_locations_for_supplier(self, db: Session, supplier_id: str) -> List[str]:
        return db.query(Whitelist.location_id).filter(Whitelist.supplier_id == supplier_id).all()

    def location_to_purchaser_id(self, db: Session, _location_id: str):
        p =  db.query(Whitelist.purchaser_id).filter_by(location_id=_location_id).first()
        if p: 
            return p[0]
        else: 
            raise UnknownPurchaserException("unknown location id")

    def purchaser_id_to_location(self, db: Session, _purchaser_id: str):
        l = db.query(Whitelist.location_id).filter_by(purchaser_id=_purchaser_id).first()
        if l: 
            return l[0]
        else: 
            raise UnknownPurchaserException("unkwown purchaser id")

    def get_whitelisted_purchaser_ids(self, db: Session, supplier_id: str):
        res_tuples = db.query(Whitelist.purchaser_id).filter_by(supplier_id = supplier_id).all()
        return [x[0] for x in res_tuples]

    def get_whitelist(self, db: Session, supplier_id: str):
        return db.query(Whitelist).filter(Whitelist.supplier_id == supplier_id).all()

    def get_whitelist_entry(self, db: Session, supplier_id: str, purchaser_id: str):
        return db.query(Whitelist).filter(Whitelist.supplier_id == supplier_id, Whitelist.purchaser_id == purchaser_id).first()

    def purchaser_is_whitelisted(self, db: Session, _supplier_id: str, _purchaser_id: str):
        exists = db.query(Whitelist).filter_by(
            supplier_id = _supplier_id
        ).filter_by(
            purchaser_id = _purchaser_id
        ).first()
        return bool(exists)

    def location_is_whitelisted(self, db: Session, _supplier_id: str, _location_id: str):
        exists = db.query(Whitelist).filter_by(
            supplier_id = _supplier_id
        ).filter_by(
            location_id = _location_id
        ).first()
        return bool(exists)

    def get_whitelisted_purchaser_from_location_id(self, db: Session, supplier_id: str, location_id: str):
        """ return a purchaser id if a given supplier has them whitelisted as customer """
        # note this is a two step query so we can get more informative error messages
        whitelist_entry = db.query(Whitelist).filter_by(location_id = location_id).first()
        if not whitelist_entry:
            raise UnknownPurchaserException(f"Cant find purchaser for order-recipient with location_id {location_id}")

        if self.purchaser_is_whitelisted(db, supplier_id, whitelist_entry.purchaser_id):
            return whitelist_entry.purchaser_id
        else: 
            raise WhitelistException(f"Purchaser {whitelist_entry.name} not whitelisted for supplier with id {whitelist_entry.supplier_id}")

    # def get_whitelist_entry_for_location(self, customer_id: str, location_id: str):
    #     return self.session.query(Whitelist).filter(Whitelist.supplier_id == customer_id and Whitelist.location_id == location_id).first()

    def insert_whitelist_entry(
        self,
        db: Session,
        supplier_id: str,
        purchaser: PurchaserInfo,
        creditline_size: int,
        apr: float,
        tenor_in_days: int
        ):
        exists = db.query(Whitelist).filter_by(
            supplier_id = supplier_id).filter_by(purchaser_id = purchaser.id).first() is not None
        if exists:
            raise DuplicateWhitelistEntryException("Whitelist entry already exists")

        # get default args from supplier-table
        supplier = crud.supplier.get(db, supplier_id)
        _creditline_size = creditline_size if creditline_size else supplier.creditline_size
        _apr = apr if apr else supplier.apr
        _tenor_in_days = tenor_in_days if tenor_in_days else supplier.tenor_in_days

        new_whitelist_entry = WhitelistCreate(
            supplier_id=supplier_id,
            purchaser_id=purchaser.id,
            location_id=purchaser.location_id,
            name=purchaser.name,
            phone=purchaser.phone,
            city=purchaser.city,
            creditline_size=_creditline_size,
            apr=_apr,
            tenor_in_days=_tenor_in_days
        )
        entry = self.create(db, obj_in=new_whitelist_entry)
        return entry.purchaser_id


    def update_whitelist_entry(
        self,
        db: Session,
        supplier_id: str,
        purchaser_id: str,
        creditline_size: int,
        apr: float,
        tenor_in_days: int
        ):
        whitelist_entry = self.get(db, supplier_id=supplier_id, purchaser_id=purchaser_id)
        if not whitelist_entry:
            raise WhitelistException("Whitelist entry doesnt exist")

        entry = self.update(
            db=db,
            db_obj=whitelist_entry,
            obj_in=WhitelistUpdate(
                # supplier_id=supplier_id, purchaser_id=purchaser_id,
                apr=apr, creditline_size=creditline_size, tenor_in_days=tenor_in_days)
        )



whitelist = WhitelistService(Whitelist)