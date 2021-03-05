from pydantic import BaseModel
from utils.common import Invoice, ShipmentStatus, FinanceStatus, LoanTerms
from typing import Dict
import datetime as dt
from datetime import timedelta

class InvoiceData(Invoice):
    """ class to store all info that we want to keep on invoices in our DB """
    # feel free to change this to an sql-alchemy class
    data: str
    tusker_id: str

def order_to_shipping_status(raw_order: Dict):
    return ShipmentStatus.AWAITING_SHIPMENT

def order_to_destination(raw_order: Dict):
    return "moon, left crater 8"

def raw_order_to_invoice(raw_order: Dict):
    """ takes a raw order and returns an object that can be saved in the DB """
    # order_as_string = pickle.dump(raw_order)
    order_as_string = 'sdfsdf'
    return InvoiceData(**{
        "data": order_as_string,
        "tusker_id": 1,
        "id": 2,
        "amount": 3,
        "shipping_status": order_to_shipping_status(raw_order),
        "status": FinanceStatus.NONE,
        "destination": order_to_destination(raw_order)
    })

def insert_invoice_into_db():
    pass


def invoice_to_terms(id: str, amount: float, start_date: dt.datetime):
    # TODO @gsVam what makes sense here?
    return LoanTerms(
        invoice_id=id,
        principal=amount,
        interest=amount * .2,
        start_date=start_date,
        collection_date=start_date + dt.timedelta(days=90)
    )