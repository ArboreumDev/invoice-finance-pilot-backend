import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient

from database import crud
from database.models import Base
from database.models import User
from database.schemas.supplier import SupplierCreate
from database.utils import reset_db
from main import app
from routes.dependencies import get_db

TEST_DB_USER = os.getenv("POSTGRES_USER")
TEST_DB_HOST = os.getenv("POSTGRES_TEST_HOST")
TEST_DB_PORT = "5432"
TEST_DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
TEST_DB_NAME = os.getenv("POSTGRES_DB")

TEST_DB_URL = (
    f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
)

engine = create_engine(
    TEST_DB_URL
)
Base.metadata.create_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    yield from override_get_db()


app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)
CUSTOMER_ID = "0001e776-c372-4ec5-8fa4-f30ab74ca631"


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
