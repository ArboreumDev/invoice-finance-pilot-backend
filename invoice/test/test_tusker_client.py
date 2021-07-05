import pytest

from invoice.tusker_client import (TUSKER_STAGING_BASE_URL,
                                   TUSKER_STAGING_TOKEN, TuskerClient,
                                   order_status_to_code, tusker_client)
from utils.constant import GURUGRUPA_CUSTOMER_ID, LOC_ID1

# NOTE: as this is not our api, we can not really test that well, so I just try to everything once


def test_init_client_invalid_credentials():
    # TODO how to raise an exception here of gracefully raise that a connection can not be established?
    tc = TuskerClient(base_url=TUSKER_STAGING_BASE_URL, token="invalidToken")
    with pytest.raises(NotImplementedError):
        tc.create_test_order([])


def test_init_client_valid_credentials():
    tc = TuskerClient(base_url=TUSKER_STAGING_BASE_URL, token=TUSKER_STAGING_TOKEN)
    tc.create_test_order([])


def test_create_test_order():
    test_id = "test_customer_id"
    # tusker_client.create_test_order(customer_id=test_id)
    inv_id, order_ref, shipment_status = tusker_client.create_test_order(
        customer_id=GURUGRUPA_CUSTOMER_ID,
        location_id=LOC_ID1
    )

    raw_order = tusker_client.track_orders(reference_numbers=[order_ref], customer_id=test_id)[0]

    assert raw_order.get("id") == inv_id
    assert raw_order.get("ref_no") == order_ref
    assert raw_order.get("status") == shipment_status
    # verify status of created order is ready to be picked up
    assert shipment_status == order_status_to_code("PLACED_AND_VALID")


# no longer possible to mark orders as something
@pytest.mark.xfail()
def test_mark_order_as():
    test_id = "test_customer_id"
    # tusker_client.create_test_order(customer_id=test_id)
    inv_id, order_ref, _ = tusker_client.create_test_order()

    # set new status
    new_status1 = "IN_TRANSIT"
    tusker_client.mark_test_order_as(inv_id, new_status1)
    raw_order = tusker_client.track_orders(reference_numbers=[order_ref], customer_id=test_id)[0]
    assert raw_order.get("status") == order_status_to_code(new_status1)

    # update status again to delivered (default)
    tusker_client.mark_test_order_as(inv_id)
    raw_order = tusker_client.track_orders(reference_numbers=[order_ref], customer_id=test_id)[0]
    assert raw_order.get("status") == order_status_to_code("DELIVERED")


@pytest.mark.skip()
def test_track_order_pagination():
    # make sure that if more than 10 orders are being tracked, they are properly paginated
    pass
