from database.exceptions import (UnknownPhoneNumberException)
from database.db import SessionLocal, session
import datetime as dt
# from database.models import Invoice, User, Supplier
from typing import Dict
# from utils.email import EmailClient, terms_to_email_body
from sqlalchemy.orm import Session
import json
# from utils.common import LoanTerms, CreditLineInfo, PaymentDetails, PurchaserInfo, RealizedTerms
# from utils.constant import DISBURSAL_EMAIL, ARBOREUM_DISBURSAL_EMAIL
import uuid
from database import crud
from database.crud.base import CRUDBase
from database.models import KYCUser
from database.schemas import KYCUserCreate, KYCUserUpdate, KYCStatus


class BusinessType(str, Enum):
    PROPRIETOR = "PROPRIETOR"
    PARTNERSHIP = "PARTNERSHIP"
    LIMITED = "LIMITED"

class ManualVerification(str, Enum):
    AOAMOA = "AOAMOA"
    PARTNERSHIP = "PARTNERSHIP"
    ITR = "ITR"
    BUSINESSITR = "BUSINESSITR"
    GST = "GST"
    BANKSTATEMENT = "BANKSTATEMENT"
    BUSINESSBANKSTATEMENT = "BUSINESSBANKSTATEMENT"
    COMPLETED = "COMPLETED"

class UserUpdateInput(CamelModel):
    phone_number: Optional[str] = None
    email: Optional[str] = None
    business_type: Optional[BusinessType] = None
    pan_number: Optional[str] = None
    residential_address: Optional[str] = None
    pan_verification_dump: Optional[str] = None
    aadhar_number: Optional[str] = None
    aadhar_verification_dump: Optional[str] = None
    bank_account: Optional[str] = None
    bank_verification_dump: Optional[str] = None
    ifsc: Optional[str] = None
    gst_number: Optional[str] = None
    gst_verification_dump: Optional[str] = None
    business_pan_number: Optional[str] = None
    business_pan_verification_dump: Optional[str] = None
    business_address: Optional[str] = None
    business_bank_account: Optional[str] = None
    business_ifsc: Optional[str] = None
    business_bank_verification_dump: Optional[str] = None

class ImageUpdateInput(CamelModel):
    bank_statement: Optional[str] = None
    pan_image: Optional[str] = None
    aadhar_image: Optional[str] = None
    proprietor_itr: Optional[str] = None
    gst_certificate: Optional[str] = None
    business_bank_statement: Optional[str] = None
    business_itr: Optional[str] = None
    partnership_deed: Optional[str] = None
    aoa_moa_certificate: Optional[str] = None


class KYCUserService(CRUDBase[KYCUser, KYCUserCreate, KYCUserUpdate]):
    def get_user(self, phone_number: str, db: Session):
        # return none if not found
        pass

    def insert_new_user(self, args, db: Session):
        # insert new user with status initial
        # empty data & images
        pass

    def _update_user_data(self, db):
        # fetch user object, decode, find relevant key and replace
        # then recode and store
        # see how to turn it into a string
        # https://fastapi.tiangolo.com/tutorial/encoder/
        # see this how to intelligably update
        # https://fastapi.tiangolo.com/tutorial/body-updates/
        pass

    def _update_user_image(self, db):
        # fetch user object, decode, find relevant key and append
        # TODO LEVEL 1: just store the image link in the []

        # TODO LEVEL 2: download image from link and store in file-path
        file = requests.get(filename)
        filepath = create_filepath()
        image_service.store(file)
        # append filepath to object

        # then recode and store
        pass

