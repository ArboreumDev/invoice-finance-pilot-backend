import time
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from starlette.status import HTTP_401_UNAUTHORIZED

from utils.common import JWTUser
from utils.constant import (JWT_ALGORITHM, JWT_EXPIRATION_TIME_MINUTES,
                            JWT_SECRET_KEY, USER_DB, USERS)

oauth_schema = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"])


def get_hashed_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(e)
        return False


# Authenticate username and password to give JWT token
def authenticate_user(user: JWTUser):
    """
    checks whether user is in DB, the given password is correct
    returns role of the user
    """
    if user.username in USERS:
        if verify_password(plain_password=user.password, hashed_password=USER_DB[user.username]["hashed_password"]):
            return USER_DB[user.username]["role"]
    # TODO throw different errors for unknown username / password (or maybe not?)
    return False


# Create access JWT token
def create_jwt_token(user: JWTUser):
    expiration = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_TIME_MINUTES)
    jwt_payload = {"sub": user.username, "exp": expiration, "role": user.role}
    jwt_token = jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return jwt_token


# Check whether JWT token is correct
def check_jwt_token_role(token: str = Depends(oauth_schema)):
    """ raise exceptions if unauthorized, else return role and username """
    try:
        jwt_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
        username = jwt_payload.get("sub")
        expiration = jwt_payload.get("exp")
        role = jwt_payload.get("role")
        print("r", role)
        if time.time() < expiration:
            if username in USERS:
                return username, role
                # return final_checks(role, auth_level)
            else:
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unknown User")
        else:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="JWT expired")
    except Exception as e:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))


# Last checking and returning the final result
# def final_checks(role: str, auth_level: str):
#     if role == "admin":
#         return True
#     if not auth_level:
#         return True
#     else:
#         return auth_level == role
