from database.exceptions import (UnknownPhoneNumberException)
import json
import pendulum
import copy
from enum import Enum
from fastapi.encoders import jsonable_encoder
from database.db import SessionLocal, session
import datetime as dt
from utils.common import CamelModel
from utils.common import CamelModel
from database.utils import serialize
# from database.models import Invoice, User, Supplier
from typing import Dict, Optional
# from utils.email import EmailClient, terms_to_email_body
from sqlalchemy.orm import Session
import json
# from utils.common import LoanTerms, CreditLineInfo, PaymentDetails, PurchaserInfo, RealizedTerms
# from utils.constant import DISBURSAL_EMAIL, ARBOREUM_DISBURSAL_EMAIL
import uuid
from database import crud
from database.image_service import image_service
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
    phone_number: str
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
    phone_number: str
    bank_statement: Optional[str] = None
    pan_image: Optional[str] = None
    aadhar_image: Optional[str] = None
    proprietor_itr: Optional[str] = None
    gst_certificate: Optional[str] = None
    business_bank_statement: Optional[str] = None
    business_itr: Optional[str] = None
    partnership_deed: Optional[str] = None
    aoa_moa_certificate: Optional[str] = None


class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NOT_REQUIRED = "NOT_REQUIRED"


AUTO_CHECK_DOCS = ["pan_image", "aadhar_image"]

def requires_manual_check(doc_name: str):
    return doc_name not in AUTO_CHECK_DOCS




class KYCUserService(CRUDBase[KYCUser, KYCUserCreate, KYCUserUpdate]):
    def get(self, phone_number: str, db: Session):
        return db.query(KYCUser).filter(KYCUser.phone_number == phone_number).first()

    def insert_new_user(self, phone_number: str, db: Session):
        """ insert new user with status initial, empty data & images """
        user_entry = self.get(phone_number, db)

        if user_entry:
            self._logger.error(f"Update target not found: {phone_number}")
            raise UnknownPhoneNumberException("KYC User already exists")

        init_data = json.dumps(jsonable_encoder({'data': {}, 'images': {}}))
        new_user = KYCUserCreate(
            phone_number=phone_number,
            status=KYCStatus.INITIAL,
            data=init_data
        )
        kyc_user = self.create(db, obj_in=new_user)
        return kyc_user

    def _update_user_data(self, update: UserUpdateInput, db: Session):
        user_entry = self.get(update.phone_number, db)
        if not user_entry:
            msg = f"Update target not found: {update.phone_number}"
            self._logger.error(msg)
            raise UnknownPhoneNumberException(msg)

        # fetch user object, decode, find relevant keys and replace
        new_data = copy.deepcopy(user_entry.data)
        new_data.get('data',{}).update(update.dict(exclude_unset=True))
        return super().update(
            db=db,
            db_obj=user_entry,
            obj_in=KYCUserUpdate(
                phone_number=update.phone_number,
                status=KYCStatus.IN_PROGRESS,
                data=serialize(new_data)
            )
        )

    def _update_user_image(self, update: ImageUpdateInput, db: Session):
        user_entry = self.get(update.phone_number, db)
        if not user_entry:
            msg = f"Update target not found: {update.phone_number}"
            self._logger.error(msg)
            raise UnknownPhoneNumberException(msg)

        # LEVEL 1: just store the image link in the []
        # - fetch user object, decode, find relevant key and append
        # create new data object to be stored and append updates
        new_user_data = copy.deepcopy(user_entry.data)
        for doc_name, image_url in update.dict(exclude_unset=True).items():
            if doc_name == "phone_number": continue
            # TODO LEVEL 2: download image from link and store in file-path
            path = image_service.fetch_and_store(image_url=image_url, doc_name=doc_name, phone_number=update.phone_number)
           # create new object with existing & new filepaths
            new_image_data = new_user_data['images'].get(
                doc_name,
                {
                    "filenames": [],
                    "upload_dates": [],
                    "verification": VerificationStatus.UNVERIFIED if requires_manual_check(doc_name=doc_name) else VerificationStatus.NOT_REQUIRED
                }
             )
            new_image_data['filenames'].append(path)
            new_image_data['upload_dates'].append(pendulum.now().int_timestamp)
            # store under new data object
            new_user_data['images'][doc_name] = new_image_data

        return super().update(
            db=db,
            db_obj=user_entry,
            obj_in=KYCUserUpdate(
                phone_number=update.phone_number,
                status=KYCStatus.IN_PROGRESS,
                data=serialize(new_user_data),
            )
        )

    def get_all_user_images(self, phone_number: str, db: Session):
        user_entry = self.get(phone_number, db)
        if not user_entry:
            msg = f"User not found: {phone_number}"
            self._logger.error(msg)
            raise UnknownPhoneNumberException(msg)

        all_filenames = []
        for image_obj in user_entry.data['images'].values():
            # print('img-ob', image_obj)
            all_filenames += image_obj['filenames']
        return all_filenames

    def create_zip_file(self, phone_number: str, db: Session):
        user_entry = self.get(phone_number, db)
        if not user_entry:
            msg = f"User not found: {phone_number}"
            self._logger.error(msg)
            raise UnknownPhoneNumberException(msg)



kyc_user = KYCUserService(KYCUser)