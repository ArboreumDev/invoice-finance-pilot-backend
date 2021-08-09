from typing import Any, Dict, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session

# from app.core.security import get_password_hash, verify_password
from database.crud.base import CRUDBase
from database.models import Invoice
from database.schemas import InvoiceCreate, InvoiceUpdate


class CRUDInvoice(CRUDBase[Invoice, InvoiceCreate, InvoiceUpdate]):

    # def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
    #     return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: InvoiceCreate) -> Invoice:
        db_obj = Invoice(
            **obj_in.dict(), 
            updated_on=datetime.now()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Invoice, obj_in: Union[InvoiceUpdate, Dict[str, Any]]
    ) -> Invoice:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db, db_obj=db_obj, obj_in=update_data)

invoice = CRUDInvoice(Invoice)