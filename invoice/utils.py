from typing import Dict

from invoice.tusker_client import code_to_order_status
from utils.common import FinanceStatus, InvoiceFrontendInfo
from database.models import Invoice


def raw_order_to_price(raw_order: Dict):
    # TODO handle error
    return raw_order.get("prc", {}).get("prc_act", 0)


def raw_order_to_invoice(raw_order: Dict):
    """ takes a raw order and returns an object that can be displayed by the frontend """
    return InvoiceFrontendInfo(
        **{
            "invoice_id": raw_order.get("id"),
            "order_id": raw_order.get("ref_no"),
            "value": raw_order_to_price(raw_order),
            "status": "NONE",
            "shipping_status": code_to_order_status(raw_order.get('status')),
        }
    )

def db_invoice_to_frontend_info(inv: Invoice):
    return InvoiceFrontendInfo(
        invoice_id=inv.id,
        order_id=inv.order_ref,
        value=inv.value,
        status=inv.finance_status,
        shipping_status=inv.shipment_status
    )
