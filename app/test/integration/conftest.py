import os

import pytest
from database import crud
from database.models import Base, User
from database.schemas.supplier import SupplierCreate
from database.schemas.purchaser import PurchaserCreate
from database.utils import reset_db
from main import app
from routes.dependencies import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient
from utils.constant import GURUGRUPA_CUSTOMER_DATA, GURUGRUPA_CUSTOMER_ID
from utils.logger import get_logger

TEST_DB_USER = os.getenv("POSTGRES_USER")
TEST_DB_HOST = os.getenv("POSTGRES_TEST_HOST")
TEST_DB_PORT = os.getenv("POSTGRES_TEST_PORT")
TEST_DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
TEST_DB_NAME = os.getenv("POSTGRES_DB")

TEST_DB_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"

engine = create_engine(TEST_DB_URL)
Base.metadata.create_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    logger = get_logger(__name__)
    logger.info("Creating DB test session")
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.info("Closed DB test session")


@pytest.fixture(scope="function")
def db_session():
    yield from override_get_db()


app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)
CUSTOMER_ID = GURUGRUPA_CUSTOMER_ID


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


def get_auth_header(username: str = "tusker", password: str = "tusker"):
    response = client.post("/token", dict(username=username, password=password))
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
            data=GURUGRUPA_CUSTOMER_DATA,
        ),
    )
    yield supplier_in_db, auth_user

    crud.supplier.remove_if_there(db_session, CUSTOMER_ID)
    reset_db(db_session)



@pytest.fixture(scope="function")
def purchaser_x_auth_user(db_session, auth_user):
    """ one user and one supplier registered """

    NEW_PURCHASER = PurchaserCreate(purchaser_id="p1", name="pname", credit_limit=1000)
    crud.purchaser.remove_if_there(db_session, NEW_PURCHASER.purchaser_id)

    purchaser_in_db = crud.purchaser.insert_new_purchaser(db_session, NEW_PURCHASER)

    yield purchaser_in_db, auth_user

    crud.purchaser.remove_if_there(db_session, NEW_PURCHASER.purchaser_id)
    reset_db(db_session)
