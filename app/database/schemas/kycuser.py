from typing import List, Optional, Dict
from pydantic import BaseModel
from enum import Enum

class KYCStatus(str, Enum):
    INITIAL = "INITIAL"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class KYCUserBase(BaseModel):
    phone_number: str 
    status: KYCStatus
    data: Dict # is this the way to tell pydantic that we store a jsonb?
    class Config:
        orm_mode = True


class KYCUserCreate(KYCUserBase):
    phone_number: str 
    pass


class KYCUserUpdate(KYCUserBase):
    pass