from enum import Enum

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


class Invoice(CamelModel):
    id: int
    amount: int
    destination: str
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