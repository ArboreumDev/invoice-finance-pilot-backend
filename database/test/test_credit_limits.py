import pytest
import copy
from database.invoice_service import InvoiceService, invoice_to_terms
from database.whitelist_service import WhitelistService
from utils.constant import MAX_CREDIT, USER_DB, RECEIVER_ID1, GURUGRUPA_CUSTOMER_ID
from database.test.fixtures import NEW_RAW_ORDER, RAW_ORDER, get_new_raw_order
from database.db import metadata, engine, session
from invoice.tusker_client import code_to_order_status, tusker_client
import contextlib
import json
from utils.constant import MAX_CREDIT, USER_DB, RECEIVER_ID1, GURUGRUPA_CUSTOMER_ID
from database.test.conftest import reset_db
import datetime as dt


invoice_service = InvoiceService()
whitelist_service = WhitelistService()


# def test_credit_line_breakdown(invoices):
#     whitelist_info = whitelist_service.get_whitelist_info_for_customer(GURUGRUPA_CUSTOMER_ID)
#     gurugrupa_receiver1 = whitelist_info[0]
#     gurugrupa_receiver2 = whitelist_info[1]
#     before = copy.deepcopy(invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID))

#     in1 = invoices[0]
#     invoice_service.update_invoice_payment_status(in1.id, "FINANCED")

#     # verify invoices with disbursed status are deducted from available credit
#     after =  invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID)

#     # note: orders are targeted to location id of receiver
#     target_id_on_invoice = in1.receiver_id
#     target_id_on_receiver_info = gurugrupa_receiver1.location_id
#     assert target_id_on_invoice == target_id_on_receiver_info

#     creditLine_id = target_id_on_receiver_info
#     assert after[creditLine_id].used  == before[creditLine_id].used + in1.value

#     # verify other credtiline is unchanged
#     other_creditLine_id = gurugrupa_receiver2.location_id
#     assert after[other_creditLine_id].available == before[other_creditLine_id].available

#     # verify consistency
#     c = after[creditLine_id]
#     c2 = before[creditLine_id]
#     print(c2)
#     assert c.available + c.used + c.requested== c.total
#     assert c2.available + c2.used + c2.requested == c2.total

#     # do the same for the DISBURSAL_REQUESTED status => iniital & disbursed are currently both shwon as requested
#     # in2 = invoices[1]
#     # invoice_service.update_invoice_payment_status(in2.id, "DISBURSAL_REQUESTED")
#     # after = invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID)
#     # assert after[gurugrupa_receiver1].used == before[gurugrupa_receiver1].used + in1.value + in2.value

# def test_credit_line_breakdown_invalid_customer_id():
#     assert invoice_service.get_credit_line_info("deadbeef") == {}


# def test_credit_line_summary(invoices):
#     # as all invoices are from one customer, they should match the invividual breakdown
#     customer = invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID)
#     summary = invoice_service.get_provider_summary("tusker")

#     assert sum(c.used for c in customer.values())== summary['gurugrupa'].used
#     assert sum(c.total for c in customer.values())== summary['gurugrupa'].total
#     assert sum(c.requested for c in customer.values())== summary['gurugrupa'].requested
#     assert sum(c.available for c in customer.values())== summary['gurugrupa'].available
#     assert sum(c.invoices for c in customer.values())== summary['gurugrupa'].invoices