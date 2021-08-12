from database.schemas import InvoiceCreate
import pytest
from database import crud
from database.db import SessionLocal, engine
from database.models import Invoice, Base, User
from database.test.fixtures import OTHER_CUSTOMER_ID, RAW_ORDER, NEW_RAW_ORDER, get_new_raw_order, p2, p1
from invoice.tusker_client import tusker_client
from utils.constant import GURUGRUPA_CUSTOMER_ID
from typing import Tuple, List
import copy
from utils.common import PurchaserInfo
from sqlalchemy.orm import Session

whitelist_service = crud.whitelist
invoice_service = crud.invoice
db: Session = SessionLocal()


def insert_base_user(db: Session):
    tusker_user = User(
        email = "tusker@mail.india",
        username = "tusker",
        hashed_password = "$2b$12$8t8LDzm.Ag68n6kv8pZoI.Oqd1x1rczNfe8QUcZwp6wnX8.dse0Ni", # pw=tusker
        role = "tusker",
    )
    # TODO use crudUser
    db.add(tusker_user)
    db.commit()

def reset_db(deleteWhitelist = False):
    db.connection().execute("delete from invoice")
    db.connection().execute("delete from invoice")
    db.connection().execute("delete from users")
    db.connection().execute("delete from supplier")
    if deleteWhitelist:
        db.connection().execute("delete from whitelist")
    db.commit()


@pytest.fixture(scope="function")
def db_session():
    _db = SessionLocal()
    try:
        yield _db
    finally:
        _db.close()


@pytest.fixture(scope="function")
def invoice1(db_session: Session) -> Tuple[Invoice, Session]:
    """ will only insert into invoices table, there will be no connected entries"""
    reset_db()
    invoice_id = invoice_service._insert_new_invoice_for_purchaser_x_supplier(RAW_ORDER, "testP", "testS", db_session)
    invoice = invoice_service.get(db_session, id=invoice_id)

    yield invoice, db_session

    reset_db()


@pytest.fixture(scope="function")
def invoices(db_session: Session) -> Tuple[List[Invoice], Session]:

    reset_db()
    insert_base_user(db_session)
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(
        get_new_raw_order(purchaser_name='p1', purchaser_location_id='l1'), 'p1', 's1', db
    )
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(
        get_new_raw_order(purchaser_name='p2', purchaser_location_id='l2'), 'p1', 's1', db
    )
    invoices = db.query(Invoice).all()

    yield invoices, db

    reset_db()

@pytest.fixture(scope="function")
def whitelisted_invoices(db_session: Session):
    reset_db(deleteWhitelist=True)
    insert_base_user(db_session)


    # create two whitelist entry for supplier
    _supplier_id=CUSTOMER_ID
    _purchaser=p1

    whitelist_service.insert_whitelist_entry(
        db_session,
        supplier_id=_supplier_id,
        purchaser=_purchaser,
        creditline_size=50000,
        apr=0.1,
        tenor_in_days=90
    )

    whitelist_service.insert_whitelist_entry(
        db_session,
        supplier_id=_supplier_id,
        purchaser=p2,
        creditline_size=40000,
        apr=0.1,
        tenor_in_days=90
    )

    # create two invoices for the first entry
    invoice_service.insert_new_invoice_from_raw_order(
        get_new_raw_order(
            purchaser_name=_purchaser.name,
            purchaser_location_id=_purchaser.location_id,
            supplier_id=_supplier_id
        ),
        db_session
    )
    invoice_service.insert_new_invoice_from_raw_order(
        get_new_raw_order(
            purchaser_name=_purchaser.name,
            purchaser_location_id=_purchaser.location_id,
            supplier_id=_supplier_id
        ),
        db_session
    )
    invoices = db_session.query(Invoice).all()

    yield invoices, db_session

    reset_db(deleteWhitelist=True)

 


CUSTOMER_ID = "0001e776-c372-4ec5-8fa4-f30ab74ca631"
p1 = PurchaserInfo(id='aa8b8369-be51-49a3-8419-3d1eb8c4146c', name='Mahantesh Medical', phone='+91-9449642927', city='Kundagol', location_id='e0f2c12d-9371-4863-a39a-0037cd6c711b')
@pytest.fixture(scope="function")
def whitelist_entry(db_session: Session) -> Tuple[PurchaserInfo, str, Session]:
    reset_db(deleteWhitelist=True)
    insert_base_user(db_session)
    whitelist_service.insert_whitelist_entry(
        db_session,
        supplier_id=CUSTOMER_ID,
        purchaser=p1,
        creditline_size=50000,
        apr=0.1,
        tenor_in_days=90
    )

    yield p1, CUSTOMER_ID, db_session

    reset_db(deleteWhitelist=True)


