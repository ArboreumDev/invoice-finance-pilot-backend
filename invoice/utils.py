import json
from typing import Dict

from database.models import Invoice
from invoice.tusker_client import code_to_order_status
from utils.common import InvoiceFrontendInfo, PaymentDetails, PurchaserInfo


def raw_order_to_price(raw_order: Dict):
    # TODO handle error
    # return raw_order.get("prc", {}).get("pr_act", 0)
    return raw_order.get("consgt", {}).get("val_dcl", 0)


def raw_order_to_receiverInfo(raw_order: Dict):
    return PurchaserInfo(
        id=raw_order.get("id"),
        name=raw_order.get("cntct").get("name"),
        phone=raw_order.get("cntct").get("phone"),
        city=raw_order.get("loc").get("addr").get("city"),
        location_id=raw_order.get("loc").get("id"),
    )


def raw_order_to_invoice(raw_order: Dict):
    """ takes a raw order and returns an object that can be displayed by the frontend """
    return InvoiceFrontendInfo(
        **{
            "invoice_id": raw_order.get("id"),
            "supplier_id": raw_order.get("cust").get("id"),
            "order_id": raw_order.get("ref_no"),
            "value": raw_order_to_price(raw_order),
            "status": "NONE",
            "shipping_status": code_to_order_status(raw_order.get("status")),
            "receiver_info": {
                "name": raw_order.get("rcvr", {}).get("cntct", {}).get("name", "not found"),
                "id": raw_order.get("rcvr", {}).get("id"),
                "city": raw_order.get("rcvr", {}).get("addr", {}).get("city", "not found"),
                "phone": raw_order.get("rcvr", {}).get("cntct", {}).get("p_mob", "not found"),
            },
            "payment_details": {},
        }
    )


def db_invoice_to_frontend_info(inv: Invoice):
    data = json.loads(inv.data)
    payment_details = json.loads(inv.payment_details)
    return InvoiceFrontendInfo(
        invoice_id=inv.id,
        supplier_id=inv.supplier_id,
        order_id=inv.order_ref,
        value=inv.value,
        status=inv.finance_status,
        shipping_status=inv.shipment_status,
        receiver_info=PurchaserInfo(
            id=inv.purchaser_id,
            name=data.get("rcvr", {}).get("cntct", {}).get("name", "not found"),
            city=data.get("rcvr", {}).get("addr", {}).get("city", "not found"),
            phone=data.get("rcvr", {}).get("cntct", {}).get("p_mob", "not found"),
        ),
        payment_details=PaymentDetails(
            request_id=payment_details.get("request_id", "unknown"),
            repayment_id=payment_details.get("repayment_id", "unknown"),
            interest=payment_details.get("interest", "unknown"),
            collection_date=payment_details.get("collection_date", "unknown"),
            start_date=payment_details.get("start_date", "unknown"),
            verification_result=payment_details.get("verification_result", ""),
        ),
    )
