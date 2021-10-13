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
    INITIAL = "INITIAL"
    # UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    AWAITING_DELIVERY = "AWAITING_DELIVERY"
    DISBURSAL_REQUESTED = "DISBURSAL_REQUESTED"
    ERROR_SENDING_REQUEST = "ERROR_SENDING_REQUEST"
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


class Terms(CamelModel):
    apr: float = 0.1
    tenor_in_days: int = 90
    creditline_size: int = 0


class PurchaserInfo(CamelModel):
    id: str = ""
    name: str = ""
    phone: str = ""
    city: str = ""
    location_id: str = ""
    terms: Terms = Terms()


class SupplierInfo(CamelModel):
    id: str = ""
    name: str = ""
    creditline_id: str = ""
    creditline_size: int = 0
    default_terms: Terms = Terms()


class Invoice(BaseInvoice):
    order_id: str
    value: int = 1
    shipping_status: str = ""
    status: FinanceStatus = FinanceStatus.INITIAL
    raw: str = ""
    receiver_info: PurchaserInfo
    # shipping_status: ShipmentStatus = ShipmentStatus.AWAITING_SHIPMENT
    # status: FinanceStatus = FinanceStatus.NONE


class PaymentDetails(CamelModel):
    request_id: str = ""
    repayment_id: str = ""
    loan_id: str = ""
    disbursal_transaction_id: str = ""
    signature_verification_result: str = ""  # whether the signature on the invoice has been verified by the loan-admin
    interest: float = 0
    principal: float = 0
    apr: float = 0
    tenor_in_days: int = 0
    collection_date: dt.date = None


class InvoiceFrontendInfo(CamelModel):
    supplier_id: str
    invoice_id: str
    order_id: str
    value: float = 1
    verified: bool = False
    shipping_status: str = ""
    status: FinanceStatus = FinanceStatus.INITIAL
    receiver_info: PurchaserInfo
    payment_details: PaymentDetails
    financed_on: str = ""
    delivered_on: str = ""
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
    invoice_id: str
    order_id: str
    loan_id: str
    principal: float
    interest: float
    apr: float
    tenor_in_days: int


class RealizedTerms(LoanTerms):
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


class CreditLineInfo(CamelModel):
    info: PurchaserInfo
    supplier_id: str
    available: float = 0
    used: float = 0
    total: float = 0
    requested: float = 0
    invoices: int = 0

class FundedInvoice(BaseModel):
    invoice_id: str
    order_id: str
    value: float
    financed_on: str
    transaction_ref: str

# dataFormat to hit asset-creation endpoint
class NewAssetCreationInput(CamelModel):
    loan_id: str
    borrower_info: str
    principal: float
    apr: float
    tenor_in_days: int
    start_date: int
    collection_frequency: str  # "daily | monthly | weekly"
    # this is a stringified object of loan-specific data: for the tusker model it will be: List[FundedInvoice]
    data: str
