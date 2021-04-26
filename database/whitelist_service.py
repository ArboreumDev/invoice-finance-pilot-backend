from utils.common import ReceiverInfo, WhiteListEntry
from typing import Dict, List

from utils.constant import WHITELIST_DB

def get_whitelist_ids_for_customer(customer_id: str,db: Dict = WHITELIST_DB) -> List[str]:
    return list(db.get(customer_id).keys())

def get_whitelist_info_for_customer(customer_id: str, db: Dict = WHITELIST_DB) -> List[WhiteListEntry]:
    return list(db.get(customer_id).values())
