import datetime as dt
from enum import Enum
from typing import Dict, List

from humps import camelize
from pydantic import BaseModel


class ShipmentStatus(str, Enum):
    AWAITING_SHIPMENT = "AWAITING_SHIPMENT"
    SHIPPING = "SHIPPING"
    DELIVERED = "DELIVERED"


class FinanceStatus(str, Enum):
    NONE = "NONE"
    FINANCED = "FINANCED"
    REPAID = "REPAID"
    DEFAULTED = "DEFAULTED"


def to_camel(string):
    return camelize(string)


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class BaseInvoice(CamelModel):
    invoice_id: str = ""


class PurchaserInfo(CamelModel):
    id: str = ""
    name: str = ""
    phone: str = ""
    city: str = ""
    location_id: str = ""


class Invoice(BaseInvoice):
    order_id: str
    value: int = 1
    destination: str = ""
    shipping_status: str = ""
    status: str = "INITIAL"
    raw: str = ""
    receiver_info: PurchaserInfo
    # shipping_status: ShipmentStatus = ShipmentStatus.AWAITING_SHIPMENT
    # status: FinanceStatus = FinanceStatus.NONE


class PaymentDetails(CamelModel):
    request_id: str = ""
    repayment_id: str = ""
    interest: float = 0
    collection_date: dt.datetime = None
    start_date: dt.datetime = None


class InvoiceFrontendInfo(BaseInvoice):
    invoice_id: str
    order_id: str
    value: float = 1
    destination: str = ""
    shipping_status: str = ""
    status: str = "INITIAL"
    receiver_info: PurchaserInfo
    payment_details: PaymentDetails
    # shipping_status: ShipmentStatus = ShipmentStatus.AWAITING_SHIPMENT
    # status: FinanceStatus = FinanceStatus.NONE


class JWTUser(BaseModel):
    username: str
    password: str
    role: str = None


class FundAllocation(BaseModel):
    total_amount: int
    lender_contributions: Dict[str, float]


class Listing(BaseModel):
    listing_id: str
    total_amount: float


class LoanTerms(BaseModel):
    order_id: str
    principal: float
    invoice_id: str
    interest: float
    start_date: dt.datetime
    collection_date: dt.datetime


class MappingInput(CamelModel):
    investor_ids: List[str]
    loan_amount: float


class Mapping(CamelModel):
    allocations: Dict[str, float]


class WhiteListEntry(BaseModel):
    receiver_info: PurchaserInfo
    credit_line_size: float


class CreditLineInfo(BaseModel):
    info: PurchaserInfo
    available: float = 0
    used: float = 0
    total: float = 0
    requested: float = 0
    invoices: int = 0
