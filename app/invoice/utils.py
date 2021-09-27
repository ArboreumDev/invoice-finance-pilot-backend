import json
from typing import Dict

from database.models import Invoice, Whitelist
from invoice.tusker_client import code_to_order_status
from utils.common import (FinanceStatus, InvoiceFrontendInfo, PaymentDetails,
                          PurchaserInfo, Terms)


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
            "status": FinanceStatus.INITIAL,
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


def db_invoice_to_frontend_info(inv: Invoice, purchaser: Whitelist):
    data = json.loads(inv.data)
    payment_details = json.loads(inv.payment_details)
    return InvoiceFrontendInfo(
        invoice_id=inv.id,
        supplier_id=inv.supplier_id,
        order_id=inv.order_ref,
        value=inv.value,
        status=inv.finance_status,
        verified=inv.verified,
        shipping_status=inv.shipment_status,
        financed_on=str(inv.financed_on) or "",  # TODO handle datetime objects properly between backend & frontend
        receiver_info=PurchaserInfo(
            id=inv.purchaser_id,
            name=data.get("rcvr", {}).get("cntct", {}).get("name", "not found"),
            city=data.get("rcvr", {}).get("addr", {}).get("city", "not found"),
            phone=data.get("rcvr", {}).get("cntct", {}).get("p_mob", "not found"),
            location_id=purchaser.location_id,
            terms=Terms(
                apr=purchaser.apr, tenor_in_days=purchaser.tenor_in_days, creditline_size=purchaser.creditline_size
            ),
        ),
        payment_details=PaymentDetails(
            request_id=payment_details.get("request_id", "unknown"),
            loan_id=payment_details.get("loan_id", "unknown"),
            apr=payment_details.get("apr", "unknown"),
            tenor_in_days=payment_details.get("tenor_in_days", "unknown"),
            disbursal_transaction_id=payment_details.get("disbursal_transaction_id", "unknown"),
            repayment_id=payment_details.get("repayment_id", "unknown"),
            interest=payment_details.get("interest", "unknown"),
            principal=payment_details.get("principal", "unknown"),
            collection_date=payment_details.get("collection_date", "TBD"),
            signature_verification_result=payment_details.get("signature_verification_result", ""),
        ),
    )
