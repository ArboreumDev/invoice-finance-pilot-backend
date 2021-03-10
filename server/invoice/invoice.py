import datetime as dt
import pickle
from datetime import datetime
from typing import Dict

from db.models import Invoice as InvoiceDBTable
from utils.common import FinanceStatus, Invoice, LoanTerms, ShipmentStatus


class InvoiceData(Invoice):
    """ class to store all info that we want to keep on invoices in our DB """

    # feel free to change this to an sql-alchemy class
    shipment_status: str
    finance_status: str
    source_id: str
    cost: float
    delivery_date: str
    created_on: datetime
    updated_on: datetime


def order_to_shipping_status(raw_order: Dict):
    return ShipmentStatus.AWAITING_SHIPMENT


def order_to_destination(raw_order: Dict):
    return "moon, left crater 8"


def raw_order_to_invoice(raw_order: Dict):
    """ takes a raw order and returns an object that can be saved in the DB """
    # Let's take this to tusker_client
    # It's tightly bounded to tusker API structure.
    order_as_string = pickle.dump(raw_order)
    return InvoiceData(
        **{
            "data": order_as_string,
            "tusker_id": 1,
            "id": 2,
            "amount": 3,
            "shipping_status": order_to_shipping_status(raw_order),
            "status": FinanceStatus.NONE,
            "destination": order_to_destination(raw_order),
        }
    )


def insert_invoice_into_db():
    """
    Should be moved to DB?
    """
    from utils.tusker_client import TuskerClient

    for response_order in TuskerClient().get_latest_invoices():
        temp = {}

        temp["cost"] = response_order.get("prc", {}).get("net_price", 0)
        temp["delivery_date"] = str(response_order.get("eta", {}))
        temp["finance_status"] = "PENDING"
        temp["source_id"] = "TUSKER"

        # if filterlogic:
        InvoiceDBTable.insert().values(**temp).execute()

    return True


def invoice_to_terms(id: str, amount: float, start_date: dt.datetime):
    # TODO @gsVam what makes sense here?
    return LoanTerms(
        invoice_id=id,
        principal=amount,
        interest=amount * 0.05,
        start_date=start_date,
        collection_date=start_date + dt.timedelta(days=90),
    )
