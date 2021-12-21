import pytest
import math
import copy
from database import crud
from sqlalchemy.orm import Session
from database.crud.invoice_service import InvoiceService
from database.crud.whitelist_service import WhitelistService
from invoice.utils import invoice_to_principal
from database.test.fixtures import get_new_raw_order
from routes.v1.supplier import SupplierUpdateInput
from utils.constant import DEFAULT_PURCHASER_LIMIT
from app.database.exceptions import (
    RelationshipLimitException, SupplierLimitException, PurchaserLimitException, CreditLimitException
)
from database.schemas import WhitelistUpdate
from utils.common import FinanceStatus

invoice_service: InvoiceService = crud.invoice
whitelist_service: WhitelistService = crud.whitelist


def test_credit_line_breakdown(whitelisted_invoices):
    invoices, db = whitelisted_invoices
    in1 = invoices[0]
    supplier_id = in1.supplier_id
    whitelist_ids = whitelist_service.get_whitelisted_purchaser_ids(db, supplier_id)

    before = copy.deepcopy(invoice_service.get_credit_line_info(supplier_id, db))

    invoice_service.update_invoice_payment_status(
        db, in1.id, "FINANCED", loan_id="l1", tx_id="tx1", disbursal_time=1632497776
    )

    # verify invoices with disbursed status are deducted from available credit
    after =  invoice_service.get_credit_line_info(supplier_id, db)

    assert after[in1.purchaser_id].used  == before[in1.purchaser_id].used + invoice_to_principal(in1)

    # verify second credit line is unaffected
    other_purchaser = whitelist_ids[1 if whitelist_ids[0] == in1.purchaser_id else 0]
    assert after[other_purchaser].available == before[other_purchaser].available

    # # verify consistency
    c = after[in1.purchaser_id]
    c2 = before[in1.purchaser_id]
    assert math.isclose(c.available + c.used + c.requested, c.total)
    assert math.isclose(c2.available + c2.used + c2.requested, c2.total)

    # do the same for the DISBURSAL_REQUESTED status => iniital & disbursed are currently both shwon as requested
    # in2 = invoices[1]
    # invoice_service.update_invoice_payment_status(in2.id, "DISBURSAL_REQUESTED")
    # after = invoice_service.get_credit_line_info(GURUGRUPA_CUSTOMER_ID)
    # assert after[gurugrupa_receiver1].used == before[gurugrupa_receiver1].used + in1.value + in2.value


def test_credit_line_breakdown_invalid_customer_id(db_session: Session):
    assert invoice_service.get_credit_line_info("deadbeef", db_session) == {}

# @pytest.mark.xfail(raises=RelationshipLimitException)
# @pytest.mark.xfail()
def test_relationship_limit(whitelisted_purchasers):
    supplier, p1, p2, db_session = whitelisted_purchasers

    new_invoice_value =p1.creditline_size + 1 
    # first assert that the new invoice value will be
    # ... below the supplier limit:
    assert supplier.creditline_size > new_invoice_value
    # ... below the (hardcoded (TODO)) purchaser limit
    assert DEFAULT_PURCHASER_LIMIT > new_invoice_value

    # try create invoice that breaks relationship limit
    # with pytest.raises(RelationshipLimitException): #TODO why does this not work
    with pytest.raises(AssertionError, match=r".*Relationship*" ):
        invoice_service.check_credit_limit(
            get_new_raw_order(
                purchaser_name=p1.name,
                purchaser_location_id=p1.location_id,
                supplier_id=supplier.supplier_id,
                value=new_invoice_value
            ),
            db_session
        )


def test_supplier_limit(whitelisted_purchasers):
    supplier, p1, p2, db_session = whitelisted_purchasers

    # update supplier limit to something too small
    supplier = crud.supplier.update(
        db_session, SupplierUpdateInput(supplier_id=supplier.supplier_id, creditline_size=300)
    )

    # try create invoice that breaks supplier limit
    new_invoice_value =supplier.creditline_size + 1 
    # with pytest.raises(SupplierLimitException):
    with pytest.raises(AssertionError, match=r".*Supplier limit*" ):
        invoice_service.check_credit_limit(
            get_new_raw_order(
                purchaser_name=p1.name,
                purchaser_location_id=p1.location_id,
                supplier_id=supplier.supplier_id,
                value=new_invoice_value
            ),
            db_session
        )
    # also assert that the new invoice value would have been
    # ... below the relationship limit:
    assert p1.creditline_size > new_invoice_value
    # ... below the (hardcoded (TODO)) purchaser limit
    assert DEFAULT_PURCHASER_LIMIT > new_invoice_value



def test_purchaser_limit(whitelisted_purchasers):
    supplier, p1, p2, db_session = whitelisted_purchasers

    # update relationship limit to something very big to not trigger
    supplier = crud.whitelist.update_whitelist_entry(
        db_session, purchaser_id=p1.purchaser_id, supplier_id=supplier.supplier_id, 
        update=WhitelistUpdate(creditline_size=300000)
    )

    # insert once invoice that is below the limit and mark it as financed
    # to check that limit takes respects invoices that already exist
    # -generate first invoice half of total purchaser limit + 25% because only 80% of each invoice are actually financed
    invoice_value = (DEFAULT_PURCHASER_LIMIT / 2) * 1.25
    first_invoice_id = crud.invoice.insert_new_invoice_from_raw_order(
        get_new_raw_order(
            purchaser_name=p1.name,
            purchaser_location_id=p1.location_id,
            supplier_id=supplier.supplier_id,
            value = invoice_value
        ),
        db_session
    )
    crud.invoice.update_invoice_payment_status(db_session, 
        invoice_id=first_invoice_id, 
        new_status=FinanceStatus.FINANCED,
        loan_id="l1",
        tx_id='tx1',
        disbursal_time=1640126947
    )

    # try create another invoice that breaks limit
    new_invoice_value = invoice_value + 1
    # before though, assert that the new invoice value will
    # ... be below the relationship limit:
    assert p1.creditline_size > invoice_value + new_invoice_value
    # ... be below the supplier limit:
    assert supplier.creditline_size > invoice_value + new_invoice_value
    # ...but be above the (hardcoded (TODO)) purchaser limit
    assert DEFAULT_PURCHASER_LIMIT < invoice_value + new_invoice_value

    # with pytest.raises(PurchaserLimitException):
    with pytest.raises(AssertionError, match=r".*Purchaser limit*" ):
        invoice_service.check_credit_limit(
            get_new_raw_order(
                purchaser_name=p1.name,
                purchaser_location_id=p1.location_id,
                supplier_id=supplier.supplier_id,
                value=invoice_value + 1
            ),
            db_session
        )


@pytest.mark.skip()
def test_credit_line_summary(whitelisted_invoices):
    supplier_id = whitelisted_invoices[0].supplier_id

    # as all invoices are from one customer, they should match the invividual breakdown
    customer = invoice_service.get_credit_line_info(supplier_id)
    # TODO refactor the user db
    # summary = invoice_service.get_provider_summary("tusker")

    # assert sum(c.used for c in customer.values())== summary['gurugrupa'].used
    # assert sum(c.total for c in customer.values())== summary['gurugrupa'].total
    # assert sum(c.requested for c in customer.values())== summary['gurugrupa'].requested
    # assert sum(c.available for c in customer.values())== summary['gurugrupa'].available
    # assert sum(c.invoices for c in customer.values())== summary['gurugrupa'].invoices


@pytest.mark.skip()
def test_insert_new_invoice_exceeds_credit_line_failure():
    pass

