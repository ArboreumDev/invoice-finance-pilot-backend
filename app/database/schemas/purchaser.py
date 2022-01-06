# following this tutorial, schemas will denote pydantics-models 
# whereas models.py will describe the SQLAlchemy models
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from pydantic import BaseModel
from utils.constant import DEFAULT_PURCHASER_LIMIT



class PurchaserBase(BaseModel):
    purchaser_id: str 
    name: str 
    credit_limit: int = DEFAULT_PURCHASER_LIMIT
    # TODO move those from whitelist to here
    # location_id: str 
    # name: str 
    # phone: str 
    # city: str 


class PurchaserCreate(PurchaserBase):
    pass

    
class PurchaserUpdate(BaseModel):
    credit_limit: Optional[int] = None

class PurchaserInDB(PurchaserBase):
    pass
