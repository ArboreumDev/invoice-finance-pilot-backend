# following this tutorial, schemas will denote pydantics-models 
# whereas models.py will describe the SQLAlchemy models
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from pydantic import BaseModel
# from utils.common import CamelModel, PurchaserInfo, PaymentDetails


class WhitelistBase(BaseModel):
    supplier_id: str 
    purchaser_id: str 
    location_id: str 
    name: str 
    phone: str 
    city: str 
    creditline_size: int
    apr: float
    tenor_in_days: int


class WhitelistCreate(WhitelistBase):
    pass
    
class WhitelistUpdate(BaseModel):
    location_id: Optional[str]
    name: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    creditline_size: Optional[int]
    apr: Optional[float]
    tenor_in_days: Optional[int]



class WhitelistInDB(WhitelistBase):
    pass

# Properties to return to client
# class Whitelist(WhitelistBase):
#     pass