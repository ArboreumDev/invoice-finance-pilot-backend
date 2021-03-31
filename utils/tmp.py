from passlib.context import CryptContext

# from utils.common import JWTUser
# from utils.security import user_exists_in_db
# from utils.constant import (
#     JWT_ALGORITHM, JWT_EXPIRATION_TIME_MINUTES, JWT_SECRET_KEY, USER_DB, user_exists_in_db
# )
# from datetime import datetime, timedelta
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from fastapi import Depends, HTTPException
# from starlette.status import HTTP_401_UNAUTHORIZED
# import jwt

# oauth_schema = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"])


def get_hashed_password(password: str):
    return pwd_context.hash(password)


print(get_hashed_password("test"))
print(get_hashed_password("admin"))
