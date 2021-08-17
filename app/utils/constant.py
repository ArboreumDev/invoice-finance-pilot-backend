# %%
import os

from dotenv import load_dotenv

from utils.common import PurchaserInfo

load_dotenv()

config_keys = [
    "JWT_SECRET_KEY",
    "EMAIL_HOST",
    "EMAIL_PASSWORD",
    "EMAIL_USERNAME",
    "EMAIL_PORT",
    "FRONTEND_URL",
    "GURUGRUPA_CUSTOMER_ID",
    "DISBURSAL_EMAIL",
    "ARBOREUM_DISBURSAL_EMAIL",
    "TUSKER_API_URL",
    "TEST_AUTH_PW",
    "GURUGRUPA_PW",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "ENVIRONMENT",
]

for key in config_keys:
    okay = True
    if not os.getenv(key):
        okay = False
        print(f"missing env variable: {key}")
    if not okay:
        raise NotImplementedError("Invalid env file")


FRONTEND_URL = os.getenv("FRONTEND_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    print("WARNING: please create a .env file!")
    # run 'openssl rand -hex 32' in terminal
    # to create a key like this:
    JWT_SECRET_KEY = "OHOc07e154e8067407c909be11132e7d1bcee77542afd6c26ba613e2ffd9c3375ea"
    print("...using a hardcoded value for now")
# %%
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_HOST = os.getenv("EMAIL_HOST")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_TIME_MINUTES = 60 * 24 * 5

# ENDPOINT DESCRIPTIONS
TOKEN_DESCRIPTION = "It checks username and password if they are true, it returns JWT token to you."

GURUGRUPA_CUSTOMER_ID = os.getenv("GURUGRUPA_CUSTOMER_ID")
print("gg is", GURUGRUPA_CUSTOMER_ID)
OTHER_CUSTOMER_ID = "6551e776-c372-4ec5-8fa4-f30ab74ca631"
ANOTHER_CUSTOMER_ID = "7551e776-c372-4ec5-8fa4-f30ab74ca631"

# these exist in tusker system
RECEIVER_ID1 = "d4dd6fee-5702-4c16-b687-75343a9af850"
RECEIVER_ID4 = "1b7ef520-70ec-490c-b533-cb06b601af5e"
LOC_ID1 = "216c6829-6439-4fcb-b7dc-d35d337e9315"
LOC_ID4 = "c3847461-c478-40db-a394-1ccc0c712dce"

# these are made up
RECEIVER_ID2 = "3be36644-3171-4441-a0f4-75ae4fef0a4b"
RECEIVER_ID3 = "316c6829-6439-4fcb-b7dc-d35d337e9315"
LOC_ID2 = "d3847461-c478-40db-a394-1ccc0c712dce"
LOC_ID3 = "g3847461-c478-40db-a394-1ccc0c712dce"

# add names
receiver1 = PurchaserInfo(id=RECEIVER_ID1, location_id=LOC_ID1, name="A B C Kirani Stores")
receiver2 = PurchaserInfo(id=RECEIVER_ID2, location_id=LOC_ID2, name="Dharwad Surgical")
receiver3 = PurchaserInfo(id=RECEIVER_ID3, location_id=LOC_ID3, name="Other amde up store")
receiver4 = PurchaserInfo(id=RECEIVER_ID4, location_id=LOC_ID4, name="new jeewan medicale")

DISBURSAL_EMAIL = os.getenv("DISBURSAL_EMAIL")
ARBOREUM_DISBURSAL_EMAIL = os.getenv("ARBOREUM_DISBURSAL_EMAIL")
GP_CONFIRMATION_MAIL = "julius@arboreum.dev"
MONTHLY_INTEREST = 0.0165
DEFAULT_LOAN_TENOR = 90  # days

TUSKER_API_URL = os.getenv("TUSKER_API_URL")

MAX_CREDIT = 50000

TUSKER_DEFAULT_NEW_ORDER = {
    "pl": {
        "cust": {"id": "01f8fd8e-7287-494a-b2ea-e12df585668c"},
        "shppr": {"id": "3776254c-cbf5-4b84-9276-8f4aa0439d0e"},
        "rcvr": {"id": "216c6829-6439-4fcb-b7dc-d35d337e9315"},
        "shipper_contact": {"o_id": "da899034-c729-418d-b70c-ea02d4796735"},
        "receiver_contact": {"o_id": RECEIVER_ID1},
        "consgt": {
            "cat": "8",
            "it_sm": 3,
            "val_dcl": 200,
            "wt_dcl": [123],
            "desc": "Shipping for testing",
            "s_pay": True,
        },
    },
    "strct": False,
}
