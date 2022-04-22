from utils.logger import get_logger
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from routes.v1.invoice import invoice_app
from routes.v1.whitelist import whitelist_app
from routes.v1.kyc import kyc_app
from routes.v1.supplier import supplier_app
from routes.v1.message import message_app
from routes.v1.accounts import accounts_app
from routes.v1.purchaser import purchaser_app
from routes.v1.admin import admin_app
from routes.v1.test import test_app
from starlette.status import HTTP_401_UNAUTHORIZED
from utils.common import JWTUser
from utils.constant import TOKEN_DESCRIPTION, FRONTEND_URL
from utils.security import (
    authenticate_user, create_jwt_token, check_jwt_token_role, RoleChecker, check_authorization
)
from sqlalchemy.orm import Session
from routes.dependencies import get_db, log_request, get_air
import os
from dotenv import load_dotenv

load_dotenv()
ADMIN_ROLE = os.getenv("LOAN_ADMIN_ROLE")
GUPSHUP_ROLE = os.getenv("GUPSHUP_ROLE")
print('gupshup role', GUPSHUP_ROLE)

origins = [
    FRONTEND_URL
]
app = FastAPI()

# app.include_router(invoice_app, prefix="/v1", dependencies=[Depends(check_jwt_token_role), Depends(log_request)])
# app.include_router(whitelist_app, prefix="/v1", dependencies=[Depends(check_jwt_token_role), Depends(log_request)])
# app.include_router(supplier_app, prefix="/v1", dependencies=[Depends(check_jwt_token_role), Depends(log_request)])
# app.include_router(purchaser_app, prefix="/v1", dependencies=[Depends(log_request)])
# app.include_router(purchaser_app, prefix="/v1", dependencies=[Depends(check_jwt_token_role), Depends(log_request)])
# app.include_router(test_app, prefix="/v1/test", dependencies=[])
app.include_router(
    admin_app,
    prefix="/v1/admin",
    dependencies=[Depends(RoleChecker(ADMIN_ROLE))],
    tags=['admin']
)
app.include_router(
    kyc_app, 
    prefix="/v1/kyc",
    # dependencies=[Depends(log_request), Depends(RoleChecker('gupshup'))],
    dependencies=[Depends(RoleChecker(GUPSHUP_ROLE))],
    tags=['kyc']
)

app.include_router(
    message_app, 
    prefix="/v1/message",
    dependencies=[Depends(log_request), Depends(check_authorization)],
    # dependencies=[Depends(check_authorization)],
    # dependencies=[Depends(log_request), Depends(RoleChecker('gupshup'))],
    tags=['message']
)

app.include_router(
    accounts_app,
    prefix="/v1/account",
    dependencies=[Depends(check_authorization)],
    tags=['account']
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def read_root(air = Depends(get_air)):
    air_data = air.health()
    try:
        c = air_data['accounts'] + air_data['kyc_entries']
        msg = 'be nice'
    except Exception as e:
        c = 0
        msg = str(e)
    return {"Hello": "World", 'health': c, 'msg': msg} 


@app.post("/token", description=TOKEN_DESCRIPTION, summary="JWT Auth", tags=["auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger = get_logger('login')
    """ create a token with role set to whatever is in our database """
    jwt_user_dict = {"username": form_data.username, "password": form_data.password}
    jwt_user = JWTUser(**jwt_user_dict)
    logger.info(f"login attempt by user {form_data.username}")

    role = authenticate_user(db, jwt_user)
    if not role:
        logger.exception("Invalid Credentials. Unknown user or invalid password")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")
    jwt_user.role = role

    jwt_token = create_jwt_token(jwt_user)
    logger.info("login successful!")
    return {"access_token": jwt_token, "role": role}
