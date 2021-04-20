# %%
import os

from dotenv import load_dotenv

from utils.common import ReceiverInfo, WhiteListEntry

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
    "TUSKER_API_URL",
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
OTHER_CUSTOMER_ID = "6551e776-c372-4ec5-8fa4-f30ab74ca631"
ANOTHER_CUSTOMER_ID = "7551e776-c372-4ec5-8fa4-f30ab74ca631"

# these exist in tusker system
RECEIVER_ID1 = "216c6829-6439-4fcb-b7dc-d35d337e9315"
RECEIVER_ID4 = "85ca2349-073d-4137-a38b-fc246a381270"

# these are made up
RECEIVER_ID2 = "3be36644-3171-4441-a0f4-75ae4fef0a4b"
RECEIVER_ID3 = "316c6829-6439-4fcb-b7dc-d35d337e9315"

# add names
receiver1 = ReceiverInfo(id=RECEIVER_ID1, name="A B C Kirani Stores")
receiver2 = ReceiverInfo(id=RECEIVER_ID2, name="Dharwad Surgical")
receiver3 = ReceiverInfo(id=RECEIVER_ID3, name="Other amde up store")
receiver4 = ReceiverInfo(id=RECEIVER_ID4, name="new jeewan medicale")

# DUMMY DB
# constructed by doing:
# "test_user": get_hashed_password("test_password"),
# "rc": get_hashed_password("test_rc"),
# "admin": get_hashed_password("admin_password")
# TODO use actual DB
USER_DB = {
    "gurugrupa": {
        # "hashed_password": "$2b$12$p3W5at39PORCphT4T5Kbx.TDvGNchgQ2mee8AdEDOcvZ8ZfafG0ZK",
        "hashed_password": "$2b$12$oxnGYBLZ2x73IaDHjd4ccuFayzCDoVfJHRqZQnjwM01Du8V8DNDS.",
        "role": "user",
        "customer_id": GURUGRUPA_CUSTOMER_ID,
    },
    # "admin": {
    #     "hashed_password": "$2b$12$EkTEXspTZJGjidCV4W3D5.YyUPU1UhC9JDAjxCHRl5a8POttPEcEq",
    #     "role": "admin",
    #     "customer_id": OTHER_CUSTOMER_ID,
    # },
    "test": {
        "hashed_password": "$2b$12$iHdjkqY330UiGG2K452dKeI9bVgOZs6r0dCgtZXe2YhlWkrchZ7I2",
        "role": "test",
        "customer_id": OTHER_CUSTOMER_ID,
    },
}


# dummy db to be replaced
WHITELIST_DB = {
    GURUGRUPA_CUSTOMER_ID: {
        RECEIVER_ID1: WhiteListEntry(receiver_info=receiver1, credit_line_size=50000),
        RECEIVER_ID2: WhiteListEntry(receiver_info=receiver2, credit_line_size=50000),
    },
    OTHER_CUSTOMER_ID: {
        RECEIVER_ID3: WhiteListEntry(receiver_info=receiver3, credit_line_size=50000),
        RECEIVER_ID4: WhiteListEntry(receiver_info=receiver4, credit_line_size=50000),
    },
    ANOTHER_CUSTOMER_ID: {
        RECEIVER_ID3: WhiteListEntry(receiver_info=receiver3, credit_line_size=50000),
        RECEIVER_ID4: WhiteListEntry(receiver_info=receiver4, credit_line_size=50000),
    },
}

USERS = list(USER_DB.keys())

DISBURSAL_EMAIL = os.getenv("DISBURSAL_EMAIL")
GP_CONFIRMATION_MAIL = "julius@arboreum.dev"
MONTHLY_INTEREST = 0.0165

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
