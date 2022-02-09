from database.crud import kyc_user as kycuser_service
from database.crud.kycuser_service import (ImageUpdateInput,
                                           ManualVerification, UserUpdateInput)
from database.exceptions import UnknownPhoneNumberException
# from database.exceptions import UnknownPurchaserException
from fastapi import APIRouter, Body, Depends, HTTPException
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

# import StringIO

kyc_app = APIRouter()


@kyc_app.post("/notification/new")
def _notify_manual_verifier(
    documentType: ManualVerification,
    # phone_number: str = Body(...)
    summary="Sends an email to the loan admin with info on the document to be manually verified",
):
    # send email to loan manager to check latest thing! as background task
    return {"status": "success"}


@kyc_app.post("/user/new", summary="Create a new user by a unique phone number")
def _create_new_user(phonenumber: str = Body(..., embed=True), db: Session = Depends(get_db)):
    new_user = kycuser_service.insert_new_user(phone_number=phonenumber, db=db)
    return new_user


@kyc_app.post("/user/data", description="add user data overwriting old data in case of conflict")
def _update_user_data(update: UserUpdateInput = Body(...), db: Session = Depends(get_db)):
    try:
        return kycuser_service._update_user_data(update, db)
    except UnknownPhoneNumberException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@kyc_app.post("/user/image", description="upload user images, appending to existing data")
def _update_user_images(update: ImageUpdateInput = Body(...), db: Session = Depends(get_db)):
    # TODO either implement scoped security or write callable dependancy instance that checks the user role
    try:
        return kycuser_service._update_user_image(update, db)
    except UnknownPhoneNumberException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
