import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database import crud
from database.db import SessionLocal
from database.models import User
from database.schemas.supplier import SupplierCreate
from main import app

client = TestClient(app)
CUSTOMER_ID = "0001e776-c372-4ec5-8fa4-f30ab74ca631"


def reset_db(db: Session, tables=[]):
    if len(tables) == 0:
        db.connection().execute("delete from invoice")
        db.connection().execute("delete from users")
        db.connection().execute("delete from supplier")
        db.connection().execute("delete from whitelist")
    else:
        for table in tables:
            db.connection().execute(f"delete from {table}")
    db.commit()


@pytest.fixture(scope="function")
def db_session():
    _db = SessionLocal()
    try:
        yield _db
    finally:
        _db.close()


@pytest.fixture(scope="function")
def clean_supplier_table(db_session):

    db_session.connection().execute("delete from supplier")
    db_session.commit()

    yield db_session

    db_session.connection().execute("delete from supplier")
    db_session.commit()


def insert_base_user(db: Session):
    tusker_user = User(
        email="tusker@mail.india",
        username="tusker",
        hashed_password="$2b$12$8t8LDzm.Ag68n6kv8pZoI.Oqd1x1rczNfe8QUcZwp6wnX8.dse0Ni",  # pw=tusker
        role="tusker",
    )
    # TODO use crudUser
    db.add(tusker_user)
    db.commit()


def get_auth_header():
    response = client.post("/token", dict(username="tusker", password="tusker"))
    if response.status_code != 200:
        raise AssertionError("Authentication failure:, original error" + str(response.json()))
    jwt_token = response.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {jwt_token}"}
    return auth_header


@pytest.fixture(scope="function")
def auth_user(db_session):
    """ empty db, except one user registered """
    db_session.connection().execute("delete from users")

    insert_base_user(db_session)
    auth_header = get_auth_header()

    yield auth_header

    db_session.connection().execute("delete from users")


@pytest.fixture(scope="function")
def supplier_x_auth_user(db_session, auth_user):
    """ one user and one supplier registered """

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
    yield supplier_in_db, auth_user, db_session

    crud.supplier.remove_if_there(db_session, CUSTOMER_ID)
    reset_db(db_session)
