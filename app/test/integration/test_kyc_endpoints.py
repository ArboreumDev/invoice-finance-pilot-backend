from database.models import User
from database.test.conftest import (db_session, insert_base_user,  # noqa: 401
                                    reset_db)
from main import app
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

client = TestClient(app)


def insert_admin_user(db: Session):
    gupshup_user = User(
        email="gupshup@mail.india",
        username="gupshup",
        hashed_password="$2b$12$8t8LDzm.Ag68n6kv8pZoI.Oqd1x1rczNfe8QUcZwp6wnX8.dse0Ni",  # pw=tusker
        role="gupshup",
    )
    loan_admin = User(
        email="loan_admin@mail.india",
        username="loan_admin",
        hashed_password="$2b$12$8t8LDzm.Ag68n6kv8pZoI.Oqd1x1rczNfe8QUcZwp6wnX8.dse0Ni",  # pw=tusker
        role="gupshup",
    )
    db.add(tusker_user)
    db.add(loan_admin)
    db.commit()


def test_zip_file():
    pass
