# following this tutorial, schemas will denote pydantics-models 
# whereas models.py will describe the SQLAlchemy models
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from pydantic import BaseModel


class SupplierBase(BaseModel):
    supplier_id: str 
    name: str 
    creditline_size: int
    default_apr: float
    default_tenor_in_days: int


class SupplierCreate(SupplierBase):
    pass

    
class SupplierUpdate():
    supplier_id: Optional[str]
    name: Optional[str]
    creditline_size: Optional[int]
    default_apr: Optional[float]
    default_tenor_in_days: Optional[int]

class SupplierInDB(SupplierBase):
    pass
