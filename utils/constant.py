# %%
import os

from dotenv import load_dotenv

load_dotenv()

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

# DUMMY DB
# constructed by doing:
# "test_user": get_hashed_password("test_password"),
# "rc": get_hashed_password("test_rc"),
# "admin": get_hashed_password("admin_password")
# TODO use actual DB
USER_DB = {
    "test": {"hashed_password": "$2b$12$p3W5at39PORCphT4T5Kbx.TDvGNchgQ2mee8AdEDOcvZ8ZfafG0ZK", "role": "user"},
    "admin": {"hashed_password": "$2b$12$EkTEXspTZJGjidCV4W3D5.YyUPU1UhC9JDAjxCHRl5a8POttPEcEq", "role": "admin"},
    "rc": {"hashed_password": "$2b$12$orWKHb1jGlMPkHalVdeiSe9o980PymTZ3HF2FeuYSE6cU2kZsgRCy", "role": "rc_admin"},
}



USERS = list(USER_DB.keys())

DISBURSAL_EMAIL = "julius@arboreum.dev"
GP_CONFIRMATION_MAIL = "julius@arboreum.dev"
MONTHLY_INTEREST = 0.0165

TUSKER_API_URL = "https://tusker-staging.logistimo.com/tusker-service/orders/search"
GURUGRUPA_CUSTOMER_ID = "58f1e776-c372-4ec5-8fa4-f30ab74ca631"

MAX_CREDIT = 50000

TUSKER_DEFAULT_NEW_ORDER = {
    "pl": {
        "cust": {"id": "01f8fd8e-7287-494a-b2ea-e12df585668c"},
        "shppr": {"id": "3776254c-cbf5-4b84-9276-8f4aa0439d0e"},
        "rcvr": {"id": "216c6829-6439-4fcb-b7dc-d35d337e9315"},
        "shipper_contact": {"o_id": "da899034-c729-418d-b70c-ea02d4796735"},
        "receiver_contact": {"o_id": "1aee8ce8-9c4c-4b7c-a790-6d8b4684e287"},
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
