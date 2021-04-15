from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
# from routes.v1.mapping import mapping_app
from routes.v1.invoice import invoice_app
from routes.v1.test import test_app
from starlette.status import HTTP_401_UNAUTHORIZED
from utils.common import JWTUser
from utils.constant import TOKEN_DESCRIPTION, FRONTEND_URL
from utils.security import authenticate_user, create_jwt_token, check_jwt_token_role


origins = [
    FRONTEND_URL
]
app = FastAPI()

# app.include_router(app_v1, prefix="/v1", dependencies=[Depends(check_jwt_token)])
# app.include_router(mapping_app, prefix="/v1", dependencies=[])
app.include_router(invoice_app, prefix="/v1", dependencies=[Depends(check_jwt_token_role)])
# app.include_router(invoice_app, prefix="/v1", dependencies=[])


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def read_root():
    return {"Hello": "World"}


@app.post("/token", description=TOKEN_DESCRIPTION, summary="JWT Auth", tags=["auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """ create a token with role set to whatever is in our database """
    jwt_user_dict = {"username": form_data.username, "password": form_data.password}
    jwt_user = JWTUser(**jwt_user_dict)

    role = authenticate_user(jwt_user)
    if not role:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")
    jwt_user.role = role

    jwt_token = create_jwt_token(jwt_user)
    return {"access_token": jwt_token, "role": role}
