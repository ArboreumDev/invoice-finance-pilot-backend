from sqlalchemy.sql.expression import update
from database import crud
from database.schemas import PurchaserCreate, PurchaserUpdate
from routes.v1.purchaser import PurchaserUpdateInput
import pytest
from typing import Tuple

from database.db import Session

from database.crud import purchaser as purchaser_service
from utils.common import PurchaserInfo
from database.test.conftest import db_session
from database.utils import reset_db
# from database.test.fixtures import CUSTOMER_ID, p1, p2, OTHER_CUSTOMER_ID, OTHER_PURCHASER_ID, OTHER_LOCATION_ID
from database.exceptions import DuplicatePurchaserEntryException, UnknownPurchaserException

NEW_PURCHASER = PurchaserCreate(purchaser_id="p1", name="pname", credit_limit=1000)

@pytest.fixture(scope='function')
def db(db_session):
    ''' yield clean db '''
    reset_db(db_session)

    yield db_session

    reset_db(db_session)


@pytest.fixture(scope='function')
def purchaser(db):
    purchaser = purchaser_service.insert_new_purchaser(db, NEW_PURCHASER)
    yield purchaser, db
 

def test_get_purchasers(purchaser):
    inserted_purchaser, db = purchaser
    purchasers = purchaser_service.get_all(db)

    assert len(purchasers) == 1
    assert purchasers[0].purchaser_id == inserted_purchaser.purchaser_id


def test_insert_new_purchaser(db):
    assert len(purchaser_service.get_all(db)) == 0

    purchaser = purchaser_service.insert_new_purchaser(db, NEW_PURCHASER)

    assert len(purchaser_service.get_all(db)) == 1

    purchaser_in_db = purchaser_service.get(db, NEW_PURCHASER.purchaser_id)

    assert purchaser_in_db is not None
    assert purchaser_in_db.purchaser_id == NEW_PURCHASER.purchaser_id
    assert purchaser_in_db.credit_limit == NEW_PURCHASER.credit_limit


def test_insert_existing_purchaser_fails(db):
    purchaser = purchaser_service.insert_new_purchaser(db, NEW_PURCHASER)

    with pytest.raises(DuplicatePurchaserEntryException):
        purchaser_service.insert_new_purchaser(db, NEW_PURCHASER)


def test_update_purchaser(db):
    purchaser = purchaser_service.insert_new_purchaser(db, NEW_PURCHASER)

    purchaser_service.update_purchaser(
        db, PurchaserUpdateInput(purchaser_id=NEW_PURCHASER.purchaser_id, credit_limit=2000)
    )

    purchaser_in_db = purchaser_service.get(db, NEW_PURCHASER.purchaser_id)
    assert purchaser_in_db.credit_limit == 2000


def test_update_nonexisting_purchaser_failss(db):
    purchaser = purchaser_service.insert_new_purchaser(db, NEW_PURCHASER)

    with pytest.raises(UnknownPurchaserException):
        purchaser_service.update_purchaser(db, PurchaserUpdateInput(purchaser_id='bogusID', credit_limit=2000))


@pytest.mark.todo()
def test_invoice_sum_by_purchaser():
    pass

