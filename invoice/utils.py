from typing import Dict

from invoice.tusker_client import code_to_order_status
from utils.common import FinanceStatus, InvoiceFrontendInfo


def raw_order_to_price(raw_order: Dict):
    # TODO handle error
    return raw_order.get("prc", {}).get("prc_act", 0)


def raw_order_to_invoice(raw_order: Dict):
    """ takes a raw order and returns an object that can be displayed by the frontend """
    return InvoiceFrontendInfo(
        **{
            # "data": order_as_string,
            # "tusker_id": 1,
            "id": raw_order.get("id"),
            "value": raw_order_to_price(raw_order),
            "shipping_status": code_to_order_status(raw_order.get('status')),
            "status": FinanceStatus.NONE,
            "order_id": raw_order.get("ref_no"),
            "finance_status": "NONE",
        }
    )
