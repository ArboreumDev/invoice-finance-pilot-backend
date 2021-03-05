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
    "test_user": {"hashed_password": "$2b$12$bLi2J2RtLNMTFiH3lE/SfuLtwk9XkECRxReGZm9Wd1ei5hY.X9RUW", "role": "user"},
    "rc": {"hashed_password": "$2b$12$orWKHb1jGlMPkHalVdeiSe9o980PymTZ3HF2FeuYSE6cU2kZsgRCy", "role": "rc_admin"},
    "admin": {"hashed_password": "$2b$12$pctc/ptXhlxEkHIknQTbw.zzYRzifEJkSuR0HwTkqtL4O.o7J30MO", "role": "admin"},
}

USERS = list(USER_DB.keys())

DISBURSAL_EMAIL = "julius@arboreum.dev"
MONTHLY_INTEREST = 0.0165