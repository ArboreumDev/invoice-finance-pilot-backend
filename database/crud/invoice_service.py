from database.schemas import InvoiceCreate
from database.exceptions import CreditLimitException, DuplicateInvoiceException, UnknownInvoiceException
from database.db import SessionLocal, session
import datetime as dt
from database.models import Invoice, User, Supplier
from typing import Dict
from invoice.tusker_client import code_to_order_status, tusker_client
from utils.email import EmailClient, terms_to_email_body
from sqlalchemy.orm import Session
import json
from utils.common import LoanTerms, CreditLineInfo, PaymentDetails, PurchaserInfo
from utils.constant import DISBURSAL_EMAIL, ARBOREUM_DISBURSAL_EMAIL
from invoice.utils import raw_order_to_price
import uuid
from database.crud.whitelist_service import  whitelist_entry_to_receiverInfo
from database import crud
from database.crud.base import CRUDBase
from database.models import Invoice
from database.schemas import InvoiceCreate, InvoiceUpdate




def invoice_to_terms(id: str, order_id: str, amount: float, start_date: dt.datetime):
    return LoanTerms(
        order_id=order_id,
        invoice_id=id,
        principal=amount,
        interest=amount * 0.05,
        start_date=start_date,
        collection_date=start_date + dt.timedelta(days=90),
    )


class InvoiceService(CRUDBase[Invoice, InvoiceCreate, InvoiceUpdate]):
    def insert_new_invoice_from_raw_order(self, raw_order: Dict, db: Session):
        # verify the customer of the order has the purchaser whitelisted
        supplier_id=raw_order.get('cust').get('id')
        location_id = raw_order.get('rcvr').get('id')
        purchaser_id = crud.whitelist.get_whitelisted_purchaser_from_location_id(db, supplier_id, location_id)
        return self._insert_new_invoice_for_purchaser_x_supplier(raw_order, purchaser_id, supplier_id, db)

    def _insert_new_invoice_for_purchaser_x_supplier(self, raw_order: Dict, purchaser_id: str, supplier_id: str, db: Session):
        exists = self.get(db, id=raw_order.get('id')) is not None

        if exists:
            raise DuplicateInvoiceException("invoice already exists")

        new_invoice = InvoiceCreate(
            id=raw_order.get("id"),
            order_ref=raw_order.get('ref_no'),
            supplier_id=supplier_id,
            purchaser_id=purchaser_id,
            shipment_status=code_to_order_status(raw_order.get('status')),
            finance_status="INITIAL",
            # TODO add default apr & tenor from whitelist-entry
            apr=0.42,
            tenor_in_days=42,
            value=raw_order_to_price(raw_order),
            data=json.dumps(raw_order),
            payment_details=json.dumps(PaymentDetails(
                requestId=str(uuid.uuid4()),
                repaymentId=str(uuid.uuid4()),
            ).dict())
        )
        invoice = self.create(db, obj_in=new_invoice)
        return invoice.id

    def update_invoice_shipment_status(self, invoice_id: str, new_status: str, db: Session):
        invoice = self.get(db, invoice_id)
        self.update_and_log(db, invoice, { "shipment_status": new_status })

    def update_and_log(self, db: Session, db_object, new_data: Dict):
        if db_object:
            update = InvoiceUpdate(**new_data, updated_on=dt.datetime.utcnow())
            return self.update(db, db_obj=db_object, obj_in=update)
        else:
            raise UnknownInvoiceException

    def update_invoice_value(self, invoice_id: str, new_value: int, db: Session):
        invoice = self.get(db, invoice_id)
        self.update_and_log(db, invoice, { "value": new_value })

    def update_invoice_payment_status(self, invoice_id: str, new_status: str, db: Session):
        invoice = self.get(db, invoice_id)
        update = {}
        if (new_status == "FINANCED"):
            self.trigger_disbursal(invoice, db)
            update['financed_on'] = dt.datetime.utcnow()
        update['finance_status'] = new_status
        return self.update_and_log(db, invoice, update)

    def update_invoice_with_loan_terms(self, invoice: Invoice, terms: LoanTerms, db: Session):
        payment_details = json.loads(invoice.payment_details)
        # TODO use pydantic json helpers
        payment_details['start_date'] = str(terms.start_date)
        payment_details['collection_date'] = str(terms.collection_date)
        payment_details['interest'] = terms.interest
        self.update_and_log(db, invoice, {'payment_details': json.dumps(payment_details)})
    
    def update_invoice_payment_details(self, invoice_id: str, new_data: Dict, db: Session):
        invoice = self.get(db, invoice_id)
        payment_details = json.loads(invoice.payment_details)
        payment_details.update(new_data)
        self.update_and_log(db, invoice, {'payment_details': json.dumps(payment_details)})

    def get_all_invoices(self, db: Session):
        # TODO use skip & limit for pagination
        return self.get_multi(db)
        # return db.query(Invoice).all()

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
        print('updating ', len(latest_raw_orders), ' orders')
        # assert len(latest_raw_orders) == len(all_reference_numbers), "update missing"

        # compare with DB if status changed
        for order in latest_raw_orders:
            new_shipment_status = code_to_order_status(order.get("status"))
            invoice = invoices[order.get("id")]
            print('updating ', order.get("ref_no"))
            if new_shipment_status != invoice.shipment_status:
                # ...if new, enact consequence and if successful update DB
                print(f"{invoice.shipment_status} -> {new_shipment_status}")
                update = {}
                try:
                    self.handle_update(invoice, new_shipment_status, db)
                    update['shipment_status'] = new_shipment_status
                    if new_shipment_status == "DELIVERED":
                        update['delivered_on'] = dt.datetime.utcnow()
                    self.update_and_log(db, invoice, update)
                    updated.append((invoice.id, new_shipment_status))
                except Exception as e:
                    print(f"ERROR handling {invoice.id}: {str(e)}")
                    errored.append((invoice.id, new_shipment_status))
            else:
                print("no update needed", invoice.shipment_status)

        return updated, errored

    def handle_update(self, invoice: Invoice, new_status: str, db: Session):
        error = ""
        if new_status == "DELIVERED":
            print('disbursal manager notified')
            self.trigger_disbursal(invoice, db)
        elif new_status == "PAID_BACK":
            print('invoice marked as repaid')
        elif new_status == "DEFAULTED":
            print('handle default')
        else:
            error += f"unprocessed invoice status {new_status} for order {invoice.order_ref}\n"

    def mark_as_paid(self, order_id: str):
        # mark as paid and reduce
        pass

    def trigger_disbursal(self, invoice: Invoice, db: Session):
        # ============== get loan terms ==========
        # calculate repayment info
        # TODO get actual invoice start date
        start_date = dt.datetime.utcnow()
        terms = invoice_to_terms(invoice.id, invoice.order_ref, invoice.value, start_date)
        self.update_invoice_with_loan_terms(invoice, terms, db)
        supplier = crud.supplier.get(db, invoice.supplier_id)
        msg = terms_to_email_body(terms, supplier.name if supplier else "TODO")

        # ================= send email to Tusker with FundRequest
        try:
            ec = EmailClient()
            ec.send_email(body=msg, subject="Arboreum Disbursal Request", targets=[DISBURSAL_EMAIL, ARBOREUM_DISBURSAL_EMAIL])
            self.update_and_log(db, invoice, {'finance_status': "DISBURSAL_REQUESTED"})
        except Exception as e:
            self.update_and_log(db, invoice, {'finance_status': "ERROR_SENDING_REQUEST"})
            raise AssertionError(f"Could not send email: {str(e)}") # TODO add custom exception


    def check_credit_limit(self, raw_order, db: Session):
        target_location_id=raw_order.get('rcvr').get('id')
        supplier_id=raw_order.get('cust').get('id')
        purchaser_id = crud.whitelist.get_whitelisted_purchaser_from_location_id(db, supplier_id, target_location_id)

        value=raw_order_to_price(raw_order)
        credit = self.get_credit_line_info(supplier_id, db)

        if credit[purchaser_id].available < value:
            raise CreditLimitException(
                f"Not enough Credit available {credit[purchaser_id].available} to fund invoice of value {value}"
            )

        return True

    # TODO turn this into a view using
    # https://stackoverflow.com/questions/9766940/how-to-create-an-sql-view-with-sqlalchemy
    def get_credit_line_info(self, supplier_id: str, db: Session):
        credit_line_breakdown = {}
        for w_entry in crud.whitelist.get_whitelist(db, supplier_id):
            credit_line_size  = w_entry.creditline_size if w_entry.creditline_size != 0 else 0

            invoices = db.query(Invoice).filter(Invoice.purchaser_id == w_entry.purchaser_id).all()
            to_be_repaid = sum(i.value for i in invoices if i.finance_status == "FINANCED")
            requested = sum(i.value for i in invoices if i.finance_status in ["DISBURSAL_REQUESTED", "INITIAL"])
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


