from test.integration.conftest import client

import pytest
from database.crud.purchaser_service import purchaser as purchaser_service
from database.schemas import PurchaserCreate
from database.utils import reset_db
from routes.v1.purchaser import PurchaserUpdateInput
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

NEW_PURCHASER = PurchaserCreate(purchaser_id="p1", name="name", credit_limit=1000)

purchaser_update = PurchaserUpdateInput(purchaser_id=NEW_PURCHASER.purchaser_id, credit_limit=50000)


# for now purchasers are created by making a new whitelist entry
@pytest.mark.skip()
def test_post_new_purchaser_entry_success(auth_user, clean_supplier_table):
    # response = client.post("v1/supplier/new", json={"input": new_supplier_input}, headers=auth_user)
    # assert response.status_code == HTTP_200_OK
    pass


@pytest.mark.skip()
def test_post_new_purchaser_duplicate_entry_failure(auth_user, clean_supplier_table):
    # response = client.post("v1/supplier/new", json={"input": new_supplier_input}, headers=auth_user)
    # assert response.status_code == HTTP_200_OK
    # response = client.post("v1/supplier/new", json={"input": NEW}, headers=auth_user)
    # assert response.status_code == HTTP_400_BAD_REQUEST
    pass


def test_get_purchasers(purchaser_x_auth_user):
    purchaser, auth_user = purchaser_x_auth_user

    response = client.get("v1/purchaser", headers=auth_user)
    assert response.status_code == HTTP_200_OK

    data = response.json()

    purchaser_from_response = [p for p in data if p["id"] == purchaser.purchaser_id][0]

    assert purchaser_from_response["creditLimit"] == purchaser.credit_limit
    assert purchaser_from_response["creditUsed"] == 0  # TODO test taht


def test_purchaser_update(purchaser_x_auth_user, db_session):
    purchaser, auth_user = purchaser_x_auth_user

    # assure new credit limit that is different from the one in the db
    new_credit_limit = purchaser.credit_limit + 4001
    # assert == purchaser_update.purchaser_id
    p_before = purchaser_service.get(db_session, purchaser.purchaser_id)
    assert p_before.credit_limit != new_credit_limit

    update = PurchaserUpdateInput(purchaser_id=purchaser.purchaser_id, credit_limit=new_credit_limit)
    response = client.post("v1/purchaser/update", json={"update": update.dict()}, headers=auth_user)
    assert response.status_code == HTTP_200_OK

    s = purchaser_service.get(db_session, update.purchaser_id)
    db_session.refresh(s)
    assert s.credit_limit == new_credit_limit

    reset_db(db_session)


def test_missing_credentials_fail(db_session):
    response = client.post("v1/purchaser/update", json={"update": purchaser_update.dict()})
    assert response.status_code == HTTP_401_UNAUTHORIZED

    response = client.get("v1/purchaser")
    assert response.status_code == HTTP_401_UNAUTHORIZED
