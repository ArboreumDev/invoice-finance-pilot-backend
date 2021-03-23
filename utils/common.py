import datetime as dt
from enum import Enum
from typing import Dict, List, Tuple
from common.loan import (Repayment as Payment, RepaymentDate as PaymentDate)

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


class Invoice(BaseInvoice):
    order_id: str
    value: int = 1
    destination: str = ""
    shipping_status: ShipmentStatus = ShipmentStatus.AWAITING_SHIPMENT
    status: FinanceStatus = FinanceStatus.NONE
    raw: str = ""


class InvoiceFrontendInfo(BaseInvoice):
    order_id: str
    value: int = 1
    destination: str = ""
    shipping_status: ShipmentStatus = ShipmentStatus.AWAITING_SHIPMENT
    status: FinanceStatus = FinanceStatus.NONE



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


class BasicTerms(CamelModel):
    loan_amount: float
    start_date: dt.datetime
    loan_type: str


class ScheduleInput(CamelModel):
    terms: BasicTerms
    disbursals: List[Payment]
    made_repayments: List[Payment]
    collection_dates: List[PaymentDate]

class RepaymentBreakdown(CamelModel):
    total: float
    principal: float
    interest: float
    penalty: float

class ScheduleOutput(CamelModel):
    scheduled_repayments: List[Tuple[RepaymentBreakdown, PaymentDate]]

class BasicScheduleOutput(CamelModel):
    repayments: List[float]
    

class CouponType(str, Enum):
    STANDARD = "STANDARD"
    BALLOON = "BALLOON"
 

class BasicCouponInput(CamelModel):
    principal: float
    apr: float
    loan_tenor: int
    collection_frequency: int
    previous_payments: List[float]
    collection_dates: List[float] = []
    apr_penalty: float = 0
    annual_compound_periods: int = 12
    collection_frequency: int = 1
    balloon_params: List[Tuple[float, str]] = []
    coupon_type: CouponType = CouponType.STANDARD

class BasicCouponOutput(CamelModel):
    coupon: Dict

