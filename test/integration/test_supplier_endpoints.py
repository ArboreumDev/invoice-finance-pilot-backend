import pytest
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from starlette.testclient import TestClient

from database.crud.supplier_service import supplier as supplier_service
from main import app
from routes.v1.supplier import SupplierInput, SupplierUpdateInput

client = TestClient(app)

new_supplier_input = SupplierInput(
    supplier_id="s1", name="supplierName", creditline_size=50000, default_apr=0.1, default_tenor_in_days=90
).dict()


def test_post_new_supplier_entry_success(auth_user, clean_supplier_table):

    response = client.post("v1/supplier/new", json={"input": new_supplier_input}, headers=auth_user)
    assert response.status_code == HTTP_200_OK


def test_post_new_supplier_duplicate_entry_failure(auth_user, clean_supplier_table):
    response = client.post("v1/supplier/new", json={"input": new_supplier_input}, headers=auth_user)
    assert response.status_code == HTTP_200_OK
    response = client.post("v1/supplier/new", json={"input": new_supplier_input}, headers=auth_user)
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_supplier_update(supplier_x_auth_user):
    supplier_in_db, auth_user, db_session = supplier_x_auth_user

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
