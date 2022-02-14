from database.crud import kyc_user as kycuser_service
from database.exceptions import UnknownPhoneNumberException, NoDocumentsException
from database.image_service import image_service
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from database.crud.kycuser_service import (VerificationStatus, ManualVerification)
from database.schemas import KYCStatus

# ===================== routes ==========================
admin_app = APIRouter()


@admin_app.get("/user/zip/{phone_number}", description="Get a zip file of all user images")
def _get_user_zip_data(phone_number: str, db: Session = Depends(get_db)):
    try:
        file_path = image_service.zip_folder(phone_number)

        def iterfile():
            with open(file_path, mode="rb") as file_like:
                yield from file_like

        return StreamingResponse(
            iterfile(),
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename={phone_number}_images.zip"},
        )
    except UnknownPhoneNumberException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@admin_app.get("/user/{phone_number}", description="Get a json blob of all user data")
def _get_user_data(phone_number: str, db: Session = Depends(get_db)):
    try:
        return kycuser_service.get(phone_number, db)
    except UnknownPhoneNumberException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@admin_app.post("/verification/document/{phone_number}", description="mark a document as verified reject it")
def _update_document_verification_status(
    phone_number: str,
    doc_type: ManualVerification,
    new_status: VerificationStatus,
    db: Session =  Depends(get_db)
):
    try:
        return kycuser_service.update_document_verification_status(
            phone_number, doc_type, new_status, db
        )
    except UnknownPhoneNumberException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    except NoDocumentsException as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


@admin_app.post("/verification/user/{phone_number}/", description="mark the entire user as verified or reject them")
def _update_verification_status(
    phone_number: str,
    newStatus: KYCStatus,
    db: Session =  Depends(get_db)
):
    try:
        return kycuser_service.update_user_verification_status(phone_number, new_status=newStatus, db=db)
    except UnknownPhoneNumberException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
