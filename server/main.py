from enum import Enum
from typing import List
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.security import check_jwt_token
from routes.v1 import app_v1
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from utils.common import (
    Invoice,
    JWTUser
)
from utils.constant import (
    TOKEN_DESCRIPTION,
)

from utils.security import (
    create_jwt_token,
    authenticate_user
)



origins = [
    "http://localhost",
    "http://localhost:3000",
]
app = FastAPI()

app.include_router(
    app_v1,
    prefix="/v1",
    dependencies=[Depends(check_jwt_token)]
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/token", description=TOKEN_DESCRIPTION, summary="JWT")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    jwt_user_dict = {"username": form_data.username, "password": form_data.password}
    jwt_user = JWTUser(**jwt_user_dict)
    

    if not authenticate_user(jwt_user):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail='Invalid Credentials'
        )

    jwt_token = create_jwt_token(jwt_user)
    return {"access_token": jwt_token}


