# following this tutorial, schemas will denote pydantics-models 
# whereas models.py will describe the SQLAlchemy models
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from pydantic import BaseModel


class SupplierBase(BaseModel):
    supplier_id: str 
    creditline_id: Optional[str] = ""
    name: str 
    data: str # data as stored as info on tusker system
    creditline_size: int
    default_apr: float
    default_tenor_in_days: int


class SupplierCreate(SupplierBase):
    pass

    
class SupplierUpdate(BaseModel):
    creditline_size: Optional[int] = None
    default_apr: Optional[float] = None
    default_tenor_in_days: Optional[int] = None
    creditline_id: Optional[str] = None

class SupplierInDB(SupplierBase):
    pass
