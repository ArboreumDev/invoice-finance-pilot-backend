from database.crud import kyc_user as kycuser_service
from database.exceptions import UnknownPhoneNumberException
from database.image_service import image_service
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from routes.dependencies import get_db
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

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
