import json
from test.integration.conftest import client

import pytest
from database.crud.supplier_service import supplier as supplier_service
from routes.v1.supplier import SupplierInput, SupplierUpdateInput
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from utils.constant import GURUGRUPA_CUSTOMER_DATA, MAX_TUSKER_CREDIT

new_supplier_input = SupplierInput(
    supplier_id="s1",
    name="supplierName",
    creditline_size=50000,
    default_apr=0.1,
    default_tenor_in_days=90,
    data=json.dumps(GURUGRUPA_CUSTOMER_DATA),
).dict()


def test_post_new_supplier_entry_success(auth_user, clean_supplier_table):

    response = client.post("v1/supplier/new", json={"input": new_supplier_input}, headers=auth_user)
    assert response.status_code == HTTP_200_OK


def test_post_new_supplier_entry_failure_credit_limit(auth_user, clean_supplier_table):
    input

    response = client.post(
        "v1/supplier/new",
        json={"input": {**new_supplier_input, "creditline_size": MAX_TUSKER_CREDIT + 2}},
        headers=auth_user,
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "Max Credit" in response.text


def test_post_new_supplier_duplicate_entry_failure(auth_user, clean_supplier_table):
    response = client.post("v1/supplier/new", json={"input": new_supplier_input}, headers=auth_user)
    assert response.status_code == HTTP_200_OK
    response = client.post("v1/supplier/new", json={"input": new_supplier_input}, headers=auth_user)
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_supplier_update(supplier_x_auth_user, db_session):
    supplier_in_db, auth_user = supplier_x_auth_user

    supplier_id = supplier_in_db.supplier_id
    new_creditline_size = 40000
    new_apr = 0.2
    # new_tenor = 90

    w_before = supplier_service.get(db_session, supplier_id)
    assert w_before.creditline_size != new_creditline_size
    assert w_before.default_apr != new_apr

    update = SupplierUpdateInput(
        supplier_id=supplier_id,
        creditline_size=new_creditline_size,
        apr=new_apr,
    ).dict()

    response = client.post("v1/supplier/update", json={"update": update}, headers=auth_user)
    assert response.status_code == HTTP_200_OK

    s = supplier_service.get(db_session, supplier_id)
    db_session.refresh(s)
    assert s.creditline_size == new_creditline_size
    assert s.default_apr == new_apr
    assert s.default_tenor_in_days == w_before.default_tenor_in_days


@pytest.mark.skip()
def test_supplier_update_fail_unknown_whitelist(auth_user):
    pass


@pytest.mark.skip()
def test_supplier_update_fail_invalid_params(auth_user):
    pass
