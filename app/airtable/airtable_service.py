import os
import pendulum
from typing import Dict
from pyairtable import Table
from dotenv import load_dotenv
from database.crud.kycuser_service import (ImageUpdateInput,
                                           ManualVerification, UserUpdateInput)
from database.exceptions import UnknownPhoneNumberException, NoDocumentsException, DuplicatePhoneNumberException

load_dotenv()
api_key = os.getenv("AIRTABLE_API_SECRET")
base_id  = os.getenv("AIRTABLE_BASE_ID")

def custom_payment_message (r):
    purpose = r.get('NEXT_REPAY_PURPOSE_MESSAGE', ['??'])
    next_amount = round(r.get('NEXT_REPAY_AMT', ['??'])[0],2)
    next_date = r.get('NEXT_DUE_DATE', ['??'])[0]
    target_name = r.get('SUPPLIER', ['??'])[0]
    full_amount = round(r.get('NEXT_REPAY_AMT', ['??'])[0],2)
    print(purpose, next_amount, next_date, target_name, full_amount )
    return f"""
    Your next payment to {target_name} in order to {purpose} is {next_amount} and is due by {next_date}.\
    If you want to repay everything today, the full amount to repay is: {full_amount} \
    """

class AirtableService():
    def __init__(self, api_key: str, base_id: str):
        self.kyc_table = Table(api_key, base_id=base_id, table_name='KYCUser')
        self.accounts_table = Table(api_key, base_id=base_id, table_name='VirtualAccounts')

    def insert_new(self, phone_number: str):
        # TODO throw error if already exists
        if self.get_record_from_phone_number(phone_number):
            raise DuplicatePhoneNumberException("KYC User already exists")
        return self.kyc_table.create({"phone_number": phone_number, 'status': "INITIAL"})

    def get_record_from_phone_number(self, phone_number: str):
        all_records = self.kyc_table.all()
        record = [r for r in all_records if r['fields'].get('phone_number', "") == phone_number]
        if len(record) > 0: return record[0]
        return None

    def update_user_data(self, phone_number: str, update: Dict):
        # TODO throw error if not exists
        r = self.get_record_from_phone_number(phone_number)
        if not r:
            raise UnknownPhoneNumberException()("KYC User does not exist")
        if 'phone_number' in update.keys(): del u['phone_number']
        return self.kyc_table.update(r['id'], update)

    def append_user_images(self, update: ImageUpdateInput):
        r = self.get_record_from_phone_number(update.phone_number)
        if not r:
            raise UnknownPhoneNumberException()("KYC User does not exist")
        # TODO throw error if not exists
        formatted_update = {}
        for key, value in update.dict(exclude_unset=True).items(): 
            if key == "phone_number": continue
            # lets get what is already there
            current = r['fields'].get(key, [])
            # and append
            filename = f"{update.phone_number}_{key}_{str(pendulum.now())[:19]}"
            formatted_update[key] = current + [{'url': value, 'filename': filename}]
        return self.kyc_table.update(r['id'], formatted_update)

    def mark_as_ready(self, phone_number: str, docType: ManualVerification):
        r = self.get_record_from_phone_number(phone_number)
        if not r:
            raise UnknownPhoneNumberException()("KYC User does not exist")
        update = {docType._to_airtable_key(): "AWAITING_VERIFICATION"}
        print('u', update)
        return self.kyc_table.update(r['id'], update)

    def get_user_payments(self, phone_number: str):
        all_records = self.accounts_table.all()
        print('all virt', all_records[0]['fields'].get('MOBILE')[0])
        repayments = [r for r in all_records if r['fields'].get('MOBILE', [None])[0] == int(phone_number)]
        print('found ', len(repayments), 'things to repay')
        msg = ""
        for r in repayments:
            msg += custom_payment_message(r['fields'])
        return msg


air_service = AirtableService(api_key, base_id)
# phone_number = '123'

# crate new
# air_service.insert_new(phone_number)

# regular data
# air.update_user_data(phone_number, {"residential_address": "moon 7"})

# ENUMS data, single value select
# air_service.update_user_data( phone_number=phone_number, update={'status':"APPROVED"})

# images
# IMAGE_URL="https://filemanager.gupshup.io/fm/wamedia/demobot1/4e735c4f-e010-4779-82bd-251cb5bfac59?fileName="
# IMAGE_URL2 = "https://images.app.goo.gl/68KYmokAF1wuF1k96"
# air_service.update_user_data(phone_number, {"pan_image": [{'url': IMAGE_URL, 'filename': "pan_image"}]})
# air_service.append_user_images(ImageUpdateInput(phone_number=phone_number, pan_image=IMAGE_URL))
# air_service.update_user_images(ImageUpdateInput(phone_number=phone_number, pan_image=IMAGE_URL2))

# r = air_service.get_record_from_phone_number(phone_number)
# print(r)