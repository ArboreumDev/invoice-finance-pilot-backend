from os import name
from utils.common import PurchaserInfo, WhiteListEntry, Terms
from typing import Dict, List
from database.exceptions import (DuplicateWhitelistEntryException, UnknownPurchaserException, WhitelistException)

from database.db import session
from database.models import Whitelist, Supplier

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


class WhitelistService():
    def __init__(self):
        self.session = session
    
    def get_whitelisted_locations_for_supplier(self, supplier_id: str) -> List[str]:
        return self.session.query(Whitelist.location_id).filter(Whitelist.supplier_id == supplier_id).all()

    def location_to_purchaser_id(self, _location_id):
        p =  self.session.query(Whitelist.purchaser_id).filter_by(location_id=_location_id).first()
        if p: 
            return p[0]
        else: 
            raise UnknownPurchaserException("unknown location id")

    def purchaser_id_to_location(self, _purchaser_id):
        l =  self.session.query(Whitelist.location_id).filter_by(purchaser_id=_purchaser_id).first()
        if l: 
            return l[0]
        else: 
            raise UnknownPurchaserException("unkwown purchaser id")

    def get_whitelisted_purchaser_ids(self, supplier_id: str):
        res_tuples = self.session.query(Whitelist.purchaser_id).filter_by(supplier_id = supplier_id).all()
        return [x[0] for x in res_tuples]

    def get_whitelist(self, supplier_id: str):
        return self.session.query(Whitelist).filter(Whitelist.supplier_id == supplier_id).all()

    def get_whitelist_entry(self, supplier_id: str, purchaser_id: str):
        return self.session.query(Whitelist).filter(Whitelist.supplier_id == supplier_id, Whitelist.purchaser_id == purchaser_id).first()

    def purchaser_is_whitelisted(self, _supplier_id: str, _purchaser_id: str):
        exists = self.session.query(Whitelist).filter_by(
            supplier_id = _supplier_id
        ).filter_by(
            purchaser_id = _purchaser_id
        ).first()
        return bool(exists)

    def location_is_whitelisted(self, _supplier_id: str, _location_id: str):
        exists = self.session.query(Whitelist).filter_by(
            supplier_id = _supplier_id
        ).filter_by(
            location_id = _location_id
        ).first()
        return bool(exists)

    def get_whitelisted_purchaser_from_location_id(self, supplier_id: str, location_id: str):
        """ return a purchaser id if a given supplier has them whitelisted as customer """
        # note this is a two step query so we can get more informative error messages
        whitelist_entry = self.session.query(Whitelist).filter_by(location_id = location_id).first()
        if not whitelist_entry:
            raise UnknownPurchaserException(f"Cant find purchaser for order-recipient with location_id {location_id}")

        if self.purchaser_is_whitelisted(supplier_id, whitelist_entry.purchaser_id):
            return whitelist_entry.purchaser_id
        else: 
            raise WhitelistException(f"Purchaser {whitelist_entry.name} not whitelisted for supplier with id {whitelist_entry.supplier_id}")

    # def get_whitelist_entry_for_location(self, customer_id: str, location_id: str):
    #     return self.session.query(Whitelist).filter(Whitelist.supplier_id == customer_id and Whitelist.location_id == location_id).first()

    def insert_whitelist_entry(
        self,
        supplier_id: str,
        purchaser: PurchaserInfo,
        creditline_size: int,
        apr: float,
        tenor_in_days: int
        ):
        exists = self.session.query(Whitelist).filter_by(
            supplier_id = supplier_id).filter_by(purchaser_id = purchaser.id).first() is not None
        if exists:
            raise DuplicateWhitelistEntryException("Whitelist entry already exists")

        # get default args from supplier-table
        supplier = self.session.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        _creditline_size = creditline_size if creditline_size else supplier.creditline_size
        _apr = apr if apr else supplier.apr
        _tenor_in_days = tenor_in_days if tenor_in_days else supplier.tenor_in_days

        new_whitelist_entry = Whitelist(
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
        self.session.add(new_whitelist_entry)
        self.session.commit()
        return new_whitelist_entry.purchaser_id


    def update_whitelist_entry(
        self,
        supplier_id: str,
        purchaser_id: str,
        creditline_size: int,
        apr: float,
        tenor_in_days: int
        ):
        whitelist_entry = self.session.query(Whitelist).filter_by(
            supplier_id = supplier_id).filter_by(purchaser_id = purchaser_id).first()
        if not whitelist_entry:
            raise WhitelistException("Whitelist entry doesnt exist")

        if not apr == None:
            whitelist_entry.apr = apr
        if not creditline_size == None:
            whitelist_entry.creditline_size = creditline_size
        if not tenor_in_days == None:
            whitelist_entry.tenor_in_days = tenor_in_days
       
        self.session.commit()


whitelist_service = WhitelistService()
