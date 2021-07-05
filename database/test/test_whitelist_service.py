import pytest
import copy
from database.service import InvoiceService, invoice_to_terms
from database.whitelist_service import WhitelistService
from utils.common import PurchaserInfo
from database.test.conftest import reset_db

whitelist_service = WhitelistService()


CUSTOMER_ID = "0001e776-c372-4ec5-8fa4-f30ab74ca631"
OTHER_CUSTOMER_ID = "3551e776-c372-4ec5-8fa4-f30ab74ca631"
PURCHASER_ID = "5551e776-c372-4ec5-8fa4-f30ab74ca631"
OTHER_PURCHASER_ID = "4551e776-c372-4ec5-8fa4-f30ab74ca631"
LOCATION_ID = "1551e776-c372-4ec5-8fa4-f30ab74ca631"
OTHER_LOCATION_ID = "0551e776-c372-4ec5-8fa4-f30ab74ca631"

p1 = PurchaserInfo(id='aa8b8369-be51-49a3-8419-3d1eb8c4146c', name='Mahantesh Medical', phone='+91-9449642927', city='Kundagol', location_id='e0f2c12d-9371-4863-a39a-0037cd6c711b')
p2 = PurchaserInfo(id='bda26d12-aee7-45e0-9686-1b173b839004', name='New Shri manjunath medical & General Store', phone='+91-9632885549', city='Haliyal', location_id='e611c64d-4dc4-4fce-b99c-93ea88b8951e')

@pytest.fixture(scope="function")
def whitelist_entry():
	reset_db(deleteWhitelist=True)
	whitelist_service.insert_whitelist_entry(
		supplier_id=CUSTOMER_ID,
		purchaser=p1,
		creditline_size=50000,
		apr=0.1,
		tenor_in_days=90
	)

	yield p1, CUSTOMER_ID

	reset_db(deleteWhitelist=True)

def test_insert_whitelist_entry():
	whitelisted = whitelist_service.get_whitelisted_locations_for_supplier(CUSTOMER_ID)
	assert len(whitelisted) == 0
	whitelist_service.insert_whitelist_entry(
		supplier_id=CUSTOMER_ID,
		purchaser=p1,
		creditline_size=50000,
		apr=0.1,
		tenor_in_days=90
	)

	whitelisted = whitelist_service.get_whitelisted_locations_for_supplier(CUSTOMER_ID)
	assert len(whitelisted) == 1
	


def test_insert_duplicate_whitelist_entry_fails(whitelist_entry):
    _p1, _customer_id = whitelist_entry
    with pytest.raises(AssertionError):
        whitelist_service.insert_whitelist_entry(
            supplier_id=_customer_id,
            purchaser=_p1,
            creditline_size=50000,
            apr=0.1,
            tenor_in_days=90
        )

def test_whitelist_okay():
    test_customer = USER_DB.get("gurugrupa").get('customer_id')
    whitelisted_receiver = whitelist_service.get_whitelisted_receivers(test_customer)[0]

    order = get_new_raw_order(
        receiver_name=whitelisted_receiver.name,
        receiver_location_id=whitelisted_receiver.location_id
    )

    assert invoice_service.is_whitelisted(order, username="gurugrupa")

# def test_whitelist_failure():
#     test_customer = USER_DB.get("gurugrupa").get('customer_id')
#     #set order receiver to something not in whitelist
#     order = copy.deepcopy(RAW_ORDER)
#     unknown_order_receiver = "0xdeadbeef"
#     order['rcvr']['id'] = unknown_order_receiver

#     assert unknown_order_receiver not in whitelist_service.get_whitelisted_purchaser_ids(test_customer)
#     assert not invoice_service.is_whitelisted(order, username="gurugrupa")


