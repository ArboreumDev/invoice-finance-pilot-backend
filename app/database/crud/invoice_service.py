from database.crud import whitelist_service
from database.schemas import whitelist
from database.schemas import InvoiceCreate
from database.exceptions import (
    RelationshipLimitException, PurchaserLimitException, SupplierLimitException, 
    DuplicateInvoiceException, UnknownInvoiceException, CreditLimitException)
from database.db import SessionLocal, session
import datetime as dt
from database.models import Invoice, User, Supplier
from typing import Dict
from invoice.tusker_client import code_to_order_status, tusker_client
from utils.email import EmailClient, terms_to_email_body
from sqlalchemy.orm import Session
import json
from utils.common import LoanTerms, CreditLineInfo, PaymentDetails, PurchaserInfo, RealizedTerms
from utils.constant import DISBURSAL_EMAIL, ARBOREUM_DISBURSAL_EMAIL
from invoice.utils import raw_order_to_price, invoice_to_principal
import uuid
from database.crud.whitelist_service import  whitelist_entry_to_receiverInfo
from database import crud
from database.crud.base import CRUDBase
from database.models import Invoice
from database.schemas import InvoiceCreate, InvoiceUpdate
from utils.common import FinanceStatus
from utils.loan import principal_to_interest
from utils.constant import INVOICE_FUNDING_RATE, DEFAULT_PURCHASER_LIMIT
from algorand.algo_service import algo_service



def invoice_to_terms(
    id: str,
    order_id: str,
    amount: float, 
    apr: float,
    tenor_in_days: int,
    loan_id: str = "TBD",
    ):
    funded_invoice_amount = INVOICE_FUNDING_RATE * amount
    return LoanTerms(
        order_id=order_id,
        invoice_id=id,
        loan_id=loan_id,
        apr=apr,
        tenor_in_days=tenor_in_days,
        principal=funded_invoice_amount,
        interest=principal_to_interest(funded_invoice_amount, apr,tenor_in_days),
    )

class InvoiceService(CRUDBase[Invoice, InvoiceCreate, InvoiceUpdate]):
    def insert_new_invoice_from_raw_order(self, raw_order: Dict, db: Session):
        # verify the customer of the order has the purchaser whitelisted
        supplier_id=raw_order.get('cust').get('id')
        location_id = raw_order.get('rcvr').get('id')
        purchaser_id = crud.whitelist.get_whitelisted_purchaser_from_location_id(db, supplier_id, location_id)
        # use this if we wanted to derive terms from whitelist
        # whitelist_entry = crud.whitelist.get_whitelist_entry(db, supplier_id, purchaser_id)
        # apr=whitelist_entry.apr,
        # tenor_in_days=whitelist_entry.tenor_in_days,
        # for now draw from supplier
        supplier = crud.supplier.get(db, supplier_id)
        apr=supplier.default_apr
        tenor_in_days=supplier.default_tenor_in_days
        return self._insert_new_invoice_for_purchaser_x_supplier(raw_order, purchaser_id, supplier_id, apr, tenor_in_days, db)

    def _insert_new_invoice_for_purchaser_x_supplier(
        self, raw_order: Dict, purchaser_id: str, supplier_id: str, apr: float, tenor_in_days: int, db: Session
    ):
        _id = raw_order.get('id')
        exists = self.get(db, id=_id) is not None

        if exists:
            self._logger.error(f"Duplicate Invoice Entry: Order {_id} already in db. Raw Order: {raw_order}")
            raise DuplicateInvoiceException(f"invoice with {_id} already exists")
        
        new_invoice = InvoiceCreate(
            id=raw_order.get("id"),
            order_ref=raw_order.get('ref_no'),
            supplier_id=supplier_id,
            purchaser_id=purchaser_id,
            shipment_status=code_to_order_status(raw_order.get('status')),
            finance_status=FinanceStatus.INITIAL,
            apr=apr,
            tenor_in_days=tenor_in_days,
            value=raw_order_to_price(raw_order),
            data=json.dumps(raw_order),
            payment_details=json.dumps(PaymentDetails(
                requestId=str(uuid.uuid4()),
                repaymentId=str(uuid.uuid4()),
                apr=apr,
                tenor_in_days=tenor_in_days
            ).dict())
        )
        invoice = self.create(db, obj_in=new_invoice)
        self.prepare_disbursal(invoice, db)
        return invoice.id

    def update_invoice_shipment_status(self, invoice_id: str, new_status: str, db: Session):
        invoice = self.get(db, invoice_id)
        self.update_and_log(db, invoice, { "shipment_status": new_status })

    def update_verification_status(self,db: Session, invoice_id: str, verified: bool):
        invoice = self.get(db, invoice_id)
        return self.update_and_log(
            db,
            invoice,
            { "verified": verified }
        )

    def update_and_log(self, db: Session, db_object, new_data: Dict):
        if db_object:
            update = InvoiceUpdate(**new_data, updated_on=dt.datetime.utcnow())
            return self.update(db, db_obj=db_object, obj_in=update)
        else:
            self._logger.error(f"Update target object not found for new_data {new_data}")
            raise UnknownInvoiceException

    def update_invoice_value(self, invoice_id: str, new_value: int, db: Session):
        invoice = self.get(db, invoice_id)
        self.update_and_log(db, invoice, { "value": new_value })

    def update_invoice_payment_status(
        self,db: Session, invoice_id: str, new_status: FinanceStatus,
        loan_id: str = "", tx_id: str = "", disbursal_time: int = 0
    ):
        invoice = self.get(db, invoice_id)
        update = {}
        if new_status == FinanceStatus.FINANCED:
            if not all([loan_id, tx_id, disbursal_time]):
                raise AssertionError("All extra finance info must be there")
            financed_on = dt.datetime.fromtimestamp(disbursal_time)
            update = {
                'payment_details': json.dumps({
                    **json.loads(invoice.payment_details),
                    'loan_id': loan_id,
                    'disbursal_transaction_id': tx_id,
                    'collection_date': str((financed_on + dt.timedelta(days=invoice.tenor_in_days)).date())
                }),
            }
            update['financed_on'] = financed_on

        if new_status == FinanceStatus.REPAID:
            self._logger.info(f"trying to log repayment of {invoice_id} on algorand chain")
            if not tx_id:
                raise AssertionError("All extra finance info must be there")
            try:
                new_tx_entry = algo_service.log_invoice_repayment(invoice_id, tx_id, db)
                # update the list of transactions associated with the asset
                # NOTE storing all that in the payment-details is starting to get messy
                # we should start using pydantics JSON-support or create a proper table for this
                # (or maybe just its own entry in the table)
                tokenization_info = json.loads(invoice.payment_details).get('tokenization', {}) # this should not empty
                # print('current tokenization', tokenization_info)
                # print('old tokenization', len(tokenization_info['transactions']))
                # print('new tx', new_tx_entry)
                tokenization_info.get('transactions').update(new_tx_entry)
                # print('new tokenization', tokenization_info)
                # print('new tokenization', len(tokenization_info['transactions']))
                crud.invoice.update_invoice_payment_details(
                    invoice_id=invoice_id, new_data={"tokenization": tokenization_info}, db=db
                )
            except Exception as e:
                self._logger.exception(f"ERROR logging payment to chain: {str(e)}")

        update['finance_status'] = new_status
        return self.update_and_log(db, invoice, update)

    def update_invoice_with_loan_terms(self, invoice: Invoice, terms: LoanTerms, db: Session):
        payment_details = json.loads(invoice.payment_details)
        # TODO use pydantic json helpers
        payment_details['loan_id'] = terms.loan_id 
        payment_details['interest'] = terms.interest
        payment_details['apr'] = terms.apr
        payment_details['tenor_in_days'] = terms.tenor_in_days
        payment_details['principal'] = terms.principal
        self.update_and_log(db, invoice, {'payment_details': json.dumps(payment_details)})
    
    def update_invoice_payment_details(self, invoice_id: str, new_data: Dict, db: Session):
        invoice = self.get(db, invoice_id)
        payment_details = json.loads(invoice.payment_details)
        payment_details.update(new_data)
        print('new data', new_data)
        self.update_and_log(db, invoice, {'payment_details': json.dumps(payment_details)})

    def get_all_invoices(self, db: Session):
        # TODO use skip & limit for pagination
        return self.get_multi(db)
    
    def get_all_invoices_from_purchaser(self, purchaser_id: str, db: Session):
        return db.query(Invoice).filter(Invoice.purchaser_id == purchaser_id).all()

    def get_sum_of_live_invoices_from_purchaser(self, purchaser_id, db: Session):
        invoices = self.get_all_invoices_from_purchaser(purchaser_id, db)
        return sum([invoice_to_principal(i)  for i in invoices if i.finance_status == FinanceStatus.FINANCED])

    def get_all_invoices_from_supplier(self, supplier_id: str, db: Session):
        return db.query(Invoice).filter(Invoice.supplier_id == supplier_id).all()

    def update_invoice_db(self, db: Session):
        """ get latest data for all invoices in db from tusker, compare shipment status,
        if changed: 
            try to process it, update DB if processing was successful
        returns (list of successful updates, list of failed updates)
        """
        updated = []
        errored = []
        # get latest data for all (TODO non-final) orders in DB
        res = db.query(Invoice).all()
        # TODO optimize by moving all filtering into the query
        invoices = {i.id: i for i in res}
        # get order_ref to track by
        all_reference_numbers = [i.order_ref for i in res]
        latest_raw_orders = tusker_client.track_orders(all_reference_numbers)
        self._logger.info(f"updating {len(latest_raw_orders)} orders")

        # compare with DB if status changed
        for order in latest_raw_orders:
            new_shipment_status = code_to_order_status(order.get("status"))
            invoice = invoices[order.get("id")]
            self._logger.info(f"updating order with ref_no: {order.get('ref_no')}")
            if new_shipment_status != invoice.shipment_status:
                # ...if new, enact consequence and if successful update DB
                self._logger.info(f"{invoice.shipment_status} -> {new_shipment_status}")
                update = {}
                try:
                    self.handle_update(db, invoice, new_shipment_status, order)
                    update['shipment_status'] = new_shipment_status
                    if new_shipment_status == "DELIVERED":
                        update['delivered_on'] = dt.datetime.utcnow()
                    self.update_and_log(db, invoice, update)
                    updated.append((invoice.id, new_shipment_status))
                except Exception as e:
                    print(f"ERROR handling {invoice.id}: {str(e)}")
                    self._logger.exception(f"ERROR handling {invoice.id}: {str(e)}")
                    errored.append((invoice.id, new_shipment_status))
            else:
                self._logger.info(f"no update needed: {invoice.shipment_status} unchanged.")

        return updated, errored

    def handle_update(self, db: Session, invoice: Invoice, new_status: str, order: Dict):
        error = ""
        if new_status == "DELIVERED":
            deliveredOn = int(order.get('s_updt', order.get('eta', ''))) / 1000
            self.update_and_log(db, invoice, {'delivered_on': dt.datetime.fromtimestamp(deliveredOn)})
            self._logger.info(f"{invoice.id} DELIVERED")
        elif new_status == "PAID_BACK":
            self._logger.info('invoice marked as repaid')
        elif new_status == "DEFAULTED":
            self._logger.info('handle default')
        else:
            error += f"unprocessed invoice status {new_status} for order {invoice.order_ref}\n"

    def mark_as_paid(self, order_id: str):
        # mark as paid and reduce
        raise NotImplementedError('TODO')

    def prepare_disbursal(self, invoice: Invoice, db: Session):
        self._logger.info(f"Updating Invoice {invoice.id} with calculated terms...")
        supplier = crud.supplier.get(db, invoice.supplier_id)
        if not supplier:
            raise UnknownInvoiceException("Invoice must belong to a supplier")
        terms = invoice_to_terms(
            id=invoice.id, order_id=invoice.order_ref, amount=invoice.value,
            apr=supplier.default_apr, tenor_in_days=supplier.default_tenor_in_days
        )
        self.update_invoice_with_loan_terms(invoice, terms, db)


    def check_credit_limit(self, raw_order, db: Session):
        """
        verify that:
        1) Relationship limit is not crossed
        2) receiver limit is not crossed
        2) purchaser limit is not crossed
        """
        target_location_id=raw_order.get('rcvr').get('id')
        supplier_id=raw_order.get('cust').get('id')
        purchaser_id = crud.whitelist.get_whitelisted_purchaser_from_location_id(db, supplier_id, target_location_id)

        value=raw_order_to_price(raw_order) * INVOICE_FUNDING_RATE
        supplier_relationships = self.get_credit_line_info(supplier_id, db)

        # 1) relationship limit
        if supplier_relationships[purchaser_id].available < value:
            # raise RelationshipLimitException(
            msg = f"Relationship limit exceeded: {supplier_relationships[purchaser_id].available} not enough \
                    to fund invoice of value {value}"
            assert False, msg
            raise RelationshipLimitException(msg) # TODO

        # 2) receiver limit not crossed
        purchaser_invoices = crud.invoice.get_all_invoices_from_purchaser(purchaser_id, db)
        total_value_financed = sum(invoice_to_principal(i) for i in purchaser_invoices if i.finance_status == FinanceStatus.FINANCED)
        purchaser = crud.purchaser.get(db, purchaser_id)
        if purchaser.credit_limit < value + total_value_financed:
            msg = f"Purchaser limit exceeded: Funded ({total_value_financed}) and invoice of value {value} \
                exceed limit ({purchaser.credit_limit})."
            assert False, msg
            raise PurchaserLimitException(msg=msg)

         # 3) supplier limit not crossed
        supplier_invoices = crud.invoice.get_all_invoices_from_supplier(supplier_id, db)
        total_value_financed = sum(invoice_to_principal(i) for i in supplier_invoices if i.finance_status == FinanceStatus.FINANCED)
        supplier = crud.supplier.get(db, supplier_id)
        if supplier.creditline_size < value + total_value_financed:
            msg = f"Supplier limit exceeded: Funded ({total_value_financed}) and invoice of value {value} \
                exceed limit ({supplier.creditline_size})."
            assert False, msg
            raise SupplierLimitException(msg)

        return True

    # TODO turn this into a view using
    # https://stackoverflow.com/questions/9766940/how-to-create-an-sql-view-with-sqlalchemy
    def get_credit_line_info(self, supplier_id: str, db: Session):
        credit_line_breakdown = {}
        for w_entry in crud.whitelist.get_whitelist(db, supplier_id):
            credit_line_size  = w_entry.creditline_size if w_entry.creditline_size != 0 else 0

            invoices = db.query(Invoice).filter(Invoice.purchaser_id == w_entry.purchaser_id).all()
            to_be_repaid = sum(invoice_to_principal(i) for i in invoices if i.finance_status == FinanceStatus.FINANCED)
            requested = sum(invoice_to_principal(i) for i in invoices if i.finance_status in [ FinanceStatus.DISBURSAL_REQUESTED, FinanceStatus.INITIAL])
            n_of_invoices = len(invoices)

            credit_line_breakdown[w_entry.purchaser_id] = CreditLineInfo(**{
                "supplier_id": supplier_id,
                "info": whitelist_entry_to_receiverInfo(w_entry),
                "total": credit_line_size,
                "available": credit_line_size - to_be_repaid - requested, #invoince.value for invoice in to_be_repaid)
                "used":to_be_repaid,
                "requested": requested,
                "invoices": n_of_invoices
            })
        return credit_line_breakdown

    def get_credit_line_summary(self, supplier_id: str, supplier_name: str, db: Session):
        summary = CreditLineInfo(info=PurchaserInfo(name=supplier_name), supplier_id="tusker")
        credit_line_breakdown = self.get_credit_line_info(supplier_id, db)
        for c in credit_line_breakdown.values():
            summary.total += c.total
            summary.available += c.available
            summary.used += c.used
            summary.requested += c.requested
            summary.invoices += c.invoices
        return summary

    def get_provider_summary(self, provider: str, db: Session):
        """ create a credit line summary for all customers whose role is user """
        credit = {}
        for supplier in crud.supplier.get_all_suppliers(db):
            credit[supplier.name] = crud.invoice.get_credit_line_summary(supplier_id=supplier.supplier_id, supplier_name=supplier.name, db=db)
        return credit



invoice = InvoiceService(Invoice)


