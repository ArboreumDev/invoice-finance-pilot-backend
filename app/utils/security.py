import time
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED

from database.models import User
from routes.dependencies import get_db
from utils.common import JWTUser
from utils.constant import (JWT_ALGORITHM, JWT_EXPIRATION_TIME_MINUTES,
                            JWT_SECRET_KEY)
from utils.logger import get_logger

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
def authenticate_user(db: Session, jwt_user: JWTUser):
    """
    checks whether user is in DB, the given password is correct
    returns role of the user
    """
    db_user = db.query(User).filter(User.username == jwt_user.username).first()
    if db_user and verify_password(plain_password=jwt_user.password, hashed_password=db_user.hashed_password):
        return db_user.role
    # TODO throw different errors for unknown username / password (or maybe not?)
    return False


# Create access JWT token
def create_jwt_token(user: JWTUser):
    expiration = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_TIME_MINUTES)
    jwt_payload = {"sub": user.username, "exp": expiration, "role": user.role}
    jwt_token = jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return jwt_token


# Check whether JWT token is correct
def check_jwt_token_role(token: str = Depends(oauth_schema), db: Session = Depends(get_db)):
    """ raise exceptions if unauthorized, else return role and username """
    logger = get_logger(__name__)
    try:
        jwt_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
        username = jwt_payload.get("sub")
        expiration = jwt_payload.get("exp")
        role = jwt_payload.get("role")
        if time.time() < expiration:
            if db.query(User).filter(User.username == username).first() is not None:
                return username, role
                # return final_checks(role, auth_level)
            else:
                logger.exception(f"Login rejected because unknown user: {username} with role {role}")
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unknown User")
        else:
            logger.exception(f"Login from {username} with role {role} rejected because JWT expired")
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="JWT expired")
    except Exception as e:
        logger.exception(f"Login rejected: {str(e)}")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))


# Last checking and returning the final result
# def final_checks(role: str, auth_level: str):
#     if role == "admin":
#         return True
#     if not auth_level:
#         return True
#     else:
#         return auth_level == role
