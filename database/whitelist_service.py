from os import name
from utils.common import PurchaserInfo, WhiteListEntry
from typing import Dict, List

from database.db import session
from database.models import Whitelist

def whitelist_entry_to_receiverInfo(entry: Whitelist):
    return PurchaserInfo(
        id=entry.receiver_id,
        name=entry.receiver_name,
        phone=entry.phone,
        city=entry.city,
        location_id=entry.location_id
    )


class WhitelistService():
    def __init__(self):
        self.session = session
    
    # def get_whitelisted_locations_for_customer(self, customer_id: str) -> List[str]:
    #     locations = self.session.query(Whitelist.location_id).filter(Whitelist.customer_id == customer_id).all()
    #     return locations

    # def get_whitelist_info_for_customer(self, customer_id: str): # -> List[WhiteListEntry]:
    #     receivers = self.session.query(Whitelist).filter(Whitelist.customer_id == customer_id).all()
    #     return [whitelist_entry_to_receiverInfo(r) for r in receivers ]


    # def get_whitelisted_purchaser_ids(self, supplier_id: str):
    #     return self.session.query(Whitelist.purchaser_id).filter(Whitelist.supplier_id == supplier_id).all()

    # def get_whitelisted_receivers(self, supplier_id: str):
    #     return self.session.query(Whitelist).filter(Whitelist.supplier_id == supplier_id).all()

    def purchaser_is_whitelisted(self, supplier_id: str, location_id: str):
        exists = self.session.query(Whitelist).filter(
            Whitelist.supplier_id == supplier_id and Whitelist.location_id == location_id
        ).first()
        return bool(exists)

    def location_is_whitelisted(self, supplier_id: str, purchaser_id: str):
        exists = self.session.query(Whitelist).filter(
            Whitelist.supplier_id == supplier_id and Whitelist.purchaser_id == purchaser_id
        ).first()
        return bool(exists)

    def get_whitelisted_purchaser_from_location_id(self, supplier_id: str, location_id: str):
        """ return a purchaser id if a given supplier has them whitelisted as customer """
        # note this is a two step query so we can get more informative error messages
        whitelist_entry = self.session.query(Whitelist).filter(Whitelist.location_id == location_id).first()
        if not whitelist_entry:
            raise AssertionError(f"Cant find purchaser for order-recipient with location_id {location_id}")

        if self.purchaser_is_whitelisted(supplier_id, whitelist_entry.purchaser_id):
            return whitelist_entry.purchaser_id
        else: 
            raise AssertionError(f"Purchaser {whitelist_entry.name} not whitelisted for customer with id {whitelist_entry.customer_id}")

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
        new_whitelist_entry = Whitelist(
            supplier_id=supplier_id,
            purchaser_id=purchaser.id,
            location_id=purchaser.location_id,
            name=purchaser.name,
            phone=purchaser.phone,
            city=purchaser.city,
            creditline_size=creditline_size,
            apr=apr,
            tenor_in_days=tenor_in_days
        )
        self.session.add(new_whitelist_entry)
        self.session.commit()
        return new_whitelist_entry.purchaser_id

whitelist_service = WhitelistService()
