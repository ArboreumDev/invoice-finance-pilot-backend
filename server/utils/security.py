from passlib.context import CryptContext
from utils.common import JWTUser
from utils.constant import (
    JWT_ALGORITHM, JWT_EXPIRATION_TIME_MINUTES, JWT_SECRET_KEY, USER_DB, USERS
)
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
import jwt
import time

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
    if user.username in USERS:
        if verify_password(plain_password=user.password, hashed_password=USER_DB[user.username]):
            return True
    # TODO throw different errors for unknown username / password (or maybe not?)
    return False


# Create access JWT token
def create_jwt_token(user: JWTUser):
    expiration = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_TIME_MINUTES)
    jwt_payload = {
        "sub": user.username,
        "exp": expiration
        # "role": user.role, 
    }
    jwt_token = jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return jwt_token

# Check whether JWT token is correct
def check_jwt_token(token: str = Depends(oauth_schema)):
    try:
        jwt_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
        username = jwt_payload.get("sub")
        expiration = jwt_payload.get("exp")
        # role = jwt_payload.get("role")
        if time.time() < expiration:
            if username in USERS:
                return final_checks() #role)
            else:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail="Unknown User"
                )
        else:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="JWT expired"
            )
    except Exception as e:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))


# Last checking and returning the final result
def final_checks():  
    # TODO do somemore complicate checks on the role
    return True