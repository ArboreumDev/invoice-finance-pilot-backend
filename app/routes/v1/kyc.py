from typing import Dict, List, Optional, Tuple
from enum import Enum

from database import crud
# from database.exceptions import UnknownPurchaserException
from fastapi import APIRouter, Body, Depends, HTTPException
# from routes.dependencies import get_db
# from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST
from utils.common import CamelModel
from utils.security import check_jwt_token_role, RoleChecker
from database.crud.kycuser_service import (
    ImageUpdateInput, UserUpdateInput, ManualVerification, BusinessType
)


kyc_app = APIRouter()

@kyc_app.post("/notification/new")
def _notify_manual_verifier(
    documentType: ManualVerification,
    # phone_number: str = Body(...)
    summary="Sends an email to the loan admin with info on the document to be manually verified"
):
    # send email to loan manager to check latest thing! as background task
    return {'status': "success"}

@kyc_app.post(
    "/user/new",
    summary="Create a new user by a unique phone number"
)
def _create_new_user(
    # phone_number: str,
):
    return {'status': "success"}

@kyc_app.post(
    "/user/data",
    description="add user data overwriting old data in case of conflict"
    )
def _update_user_data(
    update: UserUpdateInput,
):
    # update_data = update.dict(exclude_unset=True)
    return {'status': "success"}


@kyc_app.post(
    "/user/image",
    description="upload user images, appending to existing data"
    )
def _update_user_images(
    update: ImageUpdateInput,
):
    # TODO either implement scoped security or write callable dependancy instance that checks the user role
    return {'status': "success"}
