# following this tutorial, schemas will denote pydantics-models 
# whereas models.py will describe the SQLAlchemy models
# (also, in my experience models.py will describe the databases in most python backends that I saw)

from typing import List, Optional
from datetime import date, datetime, time, timedelta
from pydantic import BaseModel
from utils.common import CamelModel, PurchaserInfo, PaymentDetails

# shared properties
class InvoiceBase(BaseModel):
    pass
    # order_ref: Optional[str] = None
    # supplier_id: Optional[str] = None
    # purchaser_id: Optional[str] = None
    # shipment_status: Optional[str] = None
    # finance_status: Optional[str] = None
    # apr: Optional[float] = None
    # tenor_in_days: Optional[int] = None
    # data: Optional[str] = None
    # value: Optional[float] = None
    # payment_details: Optional[str] = None

# Properties to receive on item creation
class InvoiceCreate(InvoiceBase):
    id: str # same as in tusker system
    order_ref: str
    supplier_id: str
    purchaser_id: str
    shipment_status: str
    finance_status: str
    apr: float
    tenor_in_days: int
    data: str
    value: float
    # TODO use pydantics' json export import helpers:
    payment_details: str


# Properties stored in DB
# createInfo + stuff added by us (id, created_on, updated_on)
class InvoiceInDB(InvoiceBase):
    created_on: datetime
    updated_on: datetime
    delivered_on: datetime
    financed_on: datetime

    class Config:
        orm_mode = True


# Properties to receive on invoice update
class InvoiceUpdate(InvoiceBase):
    shipment_status: Optional[str] = None
    finance_status: Optional[str] = None
    apr: Optional[float] = None
    value: Optional[float] = None
    delivered_on: Optional[datetime] = None
    financed_on: Optional[datetime] = None


# Properties to return to client
# class Invoice(InvoiceBase):
#     id: str
#     supplier_id: str
#     order_id: str
#     value: float = 1
#     destination: str = ""
#     shipping_status: str = ""
#     status: str = "INITIAL"
#     receiver_info: PurchaserInfo
#     payment_details: PaymentDetails
 