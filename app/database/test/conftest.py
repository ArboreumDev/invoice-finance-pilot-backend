from test.integration.conftest import get_auth_header
import pytest
from database import crud
from database.models import Invoice, User, Supplier
from database.schemas.supplier import SupplierCreate
from database.test.fixtures import OTHER_CUSTOMER_ID, RAW_ORDER, NEW_RAW_ORDER, get_new_raw_order, p2, p1

from typing import Tuple, List
from utils.common import PurchaserInfo
from sqlalchemy.orm import Session

from test.integration.conftest import insert_base_user, reset_db, db_session


whitelist_service = crud.whitelist
invoice_service = crud.invoice


@pytest.fixture(scope="function")
def invoice1(db_session: Session) -> Tuple[Invoice, Session]:
    """ will only insert into invoices table, there will be no connected entries"""
    reset_db(db_session)
    invoice_id = invoice_service._insert_new_invoice_for_purchaser_x_supplier(RAW_ORDER, "testP", "testS", db_session)
    invoice = invoice_service.get(db_session, id=invoice_id)
    yield invoice, db_session

    reset_db(db_session)


@pytest.fixture(scope="function")
def invoices(db_session: Session) -> Tuple[List[Invoice], Session]:

    reset_db(db_session)
    insert_base_user(db_session)
    auth_header = get_auth_header()
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(
        get_new_raw_order(purchaser_name='p1', purchaser_location_id='l1'), 'p1', 's1', db_session
    )
    invoice_service._insert_new_invoice_for_purchaser_x_supplier(
        get_new_raw_order(purchaser_name='p2', purchaser_location_id='l2'), 'p1', 's1', db_session
    )
    invoices = db_session.query(Invoice).all()

    yield invoices, db_session

    reset_db(db_session)


@pytest.fixture(scope="function")
def whitelisted_invoices(db_session: Session):
    reset_db(db_session, deleteWhitelist=True)
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

    reset_db(db_session, deleteWhitelist=True)


CUSTOMER_ID = "0001e776-c372-4ec5-8fa4-f30ab74ca631"


@pytest.fixture(scope="function")
def whitelist_entry(db_session: Session) -> Tuple[PurchaserInfo, str, Session]:
    reset_db(db_session, deleteWhitelist=True)
    insert_base_user(db_session)
    auth_header = get_auth_header()
    whitelist_service.insert_whitelist_entry(
        db_session,
        supplier_id=CUSTOMER_ID,
        purchaser=p1,
        creditline_size=50000,
        apr=0.1,
        tenor_in_days=90
    )

    yield p1, CUSTOMER_ID, db_session

    reset_db(db_session, deleteWhitelist=True)


@pytest.fixture(scope="function")
def supplier_entry(db_session) -> Tuple[Supplier, Session]:
    crud.supplier.remove_if_there(db_session, CUSTOMER_ID)

    supplier_in_db = crud.supplier.create(
        db=db_session,
        obj_in=SupplierCreate(
            supplier_id=CUSTOMER_ID,
            name="TestSupplier",
            creditline_size=400000000,
            default_apr=0.142,
            default_tenor_in_days=90,
        ),
    )
    yield supplier_in_db, db_session

    crud.supplier.remove_if_there(db_session, CUSTOMER_ID)

