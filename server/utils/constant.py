# TODO get this from .env
# run 'openssl rand -hex 32' in terminal to create this key:
JWT_SECRET_KEY = "c07e154e8067407c909be11132e7d1bcee77542afd6c26ba613e2ffd9c3375ea"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_TIME_MINUTES = 60 * 24 * 5

# ENDPOINT DESCRIPTIONS
TOKEN_DESCRIPTION = "It checks username and password if they are true, it returns JWT token to you."

# DUMMY DB
# constructed by doing:
# "test_user": get_hashed_password("test_password"),
# "admin": get_hashed_password("admin_password")
# TODO use actual DB
USER_DB = {
    "test_user": "$2b$12$bLi2J2RtLNMTFiH3lE/SfuLtwk9XkECRxReGZm9Wd1ei5hY.X9RUW",
    "admin": "$2b$12$pctc/ptXhlxEkHIknQTbw.zzYRzifEJkSuR0HwTkqtL4O.o7J30MO",
}

USERS = list(USER_DB.keys())
