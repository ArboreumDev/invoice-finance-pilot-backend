import pytest
from invoice.tusker_client import (
    tusker_client, code_to_order_status, order_status_to_code, TUSKER_STAGING_BASE_URL, TUSKER_STAGING_TOKEN,
    TuskerClient
)

# NOTE: as this is not our api, we can not really test that well, so I just try to everything once

def test_init_client_invalid_credentials():
    # TODO how to raise an exception here of gracefully raise that a connection can not be established?
    tc = TuskerClient(base_url=TUSKER_STAGING_BASE_URL, token="invalidToken")
    with pytest.raises(Exception):
        tc.track_orders([])

def test_init_client_valid_credentials():
    tc = TuskerClient(base_url=TUSKER_STAGING_BASE_URL, token=TUSKER_STAGING_TOKEN)
    tc.track_orders([])


def test_create_test_order():
    test_id = "test_customer_id"
    # tusker_client.create_test_order(customer_id=test_id)
    inv_id, order_ref, shipment_status = tusker_client.create_test_order()

    raw_order = tusker_client.track_orders(reference_numbers=[order_ref], customer_id=test_id)[0]

    assert raw_order.get("id") == inv_id
    assert raw_order.get('ref_no') == order_ref
    assert raw_order.get('status') == shipment_status
    # verify status of created order is ready to be picked up
    assert shipment_status == order_status_to_code("PLACED_AND_VALID")


def test_mark_order_as():
    test_id = "test_customer_id"
    # tusker_client.create_test_order(customer_id=test_id)
    inv_id, order_ref, _ = tusker_client.create_test_order()

    # set new status
    new_status1 = "IN_TRANSIT"
    tusker_client.mark_test_order_as(inv_id, new_status1)
    raw_order = tusker_client.track_orders(reference_numbers=[order_ref], customer_id=test_id)[0]
    assert raw_order.get('status') == order_status_to_code(new_status1)

    # update status again to delivered (default)
    tusker_client.mark_test_order_as(inv_id)
    raw_order = tusker_client.track_orders(reference_numbers=[order_ref], customer_id=test_id)[0]
    assert raw_order.get('status') == order_status_to_code("DELIVERED")
