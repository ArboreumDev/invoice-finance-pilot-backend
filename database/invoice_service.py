from database.exceptions import CreditLimitException, DuplicateInvoiceException
from database.db import session
import datetime as dt
from database.models import Invoice, User, Supplier
from typing import Dict
from invoice.tusker_client import code_to_order_status, tusker_client
from utils.email import EmailClient, terms_to_email_body
import json
from utils.common import LoanTerms, CreditLineInfo, PaymentDetails, PurchaserInfo
from utils.constant import DISBURSAL_EMAIL, ARBOREUM_DISBURSAL_EMAIL
from invoice.utils import raw_order_to_price
import uuid
from database.whitelist_service import  whitelist_service, whitelist_entry_to_receiverInfo


def invoice_to_terms(id: str, order_id: str, amount: float, start_date: dt.datetime):
    return LoanTerms(
        order_id=order_id,
        invoice_id=id,
        principal=amount,
        interest=amount * 0.05,
        start_date=start_date,
        collection_date=start_date + dt.timedelta(days=90),
    )


class InvoiceService():
    def __init__(self):
        self.session = session

    def insert_new_invoice_from_raw_order(self, raw_order: Dict):
        # verify the customer of the order has the purchaser whitelisted
        supplier_id=raw_order.get('cust').get('id')
        location_id = raw_order.get('rcvr').get('id')
        purchaser_id = whitelist_service.get_whitelisted_purchaser_from_location_id(supplier_id, location_id)
        return self._insert_new_invoice_for_purchaser_x_supplier(raw_order, purchaser_id, supplier_id)

    def _insert_new_invoice_for_purchaser_x_supplier(self, raw_order: Dict, purchaser_id: str, supplier_id: str):
        exists = self.session.query(Invoice.id).filter_by(id=raw_order.get('id')).first() is not None
        if exists:
            raise DuplicateInvoiceException("invoice already exists")

        new_invoice = Invoice(
            id=raw_order.get("id"),
            order_ref=raw_order.get('ref_no'),
            shipment_status=code_to_order_status(raw_order.get('status')),
            finance_status="INITIAL",
            purchaser_id=purchaser_id,
            value=raw_order_to_price(raw_order),
            supplier_id=supplier_id,
            data=json.dumps(raw_order),
            payment_details=json.dumps(PaymentDetails(
                requestId=str(uuid.uuid4()),
                repaymentId=str(uuid.uuid4()),
            ).dict())
        )
        self.session.add(new_invoice)
        self.session.commit()
        return new_invoice.id

    def update_invoice_shipment_status(self, invoice_id: str, new_status: str):
        invoice = self.session.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.shipment_status = new_status
        self.session.commit()

    def update_invoice_value(self, invoice_id: str, new_value: int):
        invoice = self.session.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.value = new_value
        self.session.commit()

    def update_invoice_payment_status(self, invoice_id: str, new_status: str):
        invoice = self.session.query(Invoice).filter(Invoice.id == invoice_id).first()
        if (new_status == "FINANCED"):
            self.trigger_disbursal(invoice)
            invoice.financed_on = dt.datetime.utcnow()
        invoice.finance_status = new_status
        self.session.commit()
        return invoice

    def update_invoice_with_loan_terms(self, invoice: Invoice, terms: LoanTerms):
        payment_details = json.loads(invoice.payment_details)
        payment_details['start_date'] = str(terms.start_date)
        payment_details['collection_date'] = str(terms.collection_date)
        payment_details['interest'] = terms.interest
        invoice.payment_details = json.dumps(payment_details)
        self.session.commit()

    def delete_invoice(self, invoice_id: str):
        invoice = self.session.query(Invoice).filter(Invoice.id == invoice_id).first()
        self.session.delete(invoice)
        self.session.commit()

    def get_all_invoices(self):
        return self.session.query(Invoice).all()

    def update_invoice_db(self):
        """ get latest data for all invoices in db from tusker, compare shipment status,
        if changed: 
            try to process it, update DB if processing was successful
        returns (list of successful updates, list of failed updates)
        """
        updated = []
        errored = []
        # get latest data for all (TODO non-final) orders in DB
        res = self.session.query(Invoice).all()
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
                try:
                    self.handle_update(invoice, new_shipment_status)
                    invoice.shipment_status = new_shipment_status
                    if new_shipment_status == "DELIVERED":
                        invoice.delivered_on = dt.datetime.utcnow()
                    # invoice.updated_on = dt.datetime.utcnow()
                    self.session.commit()
                    updated.append((invoice.id, new_shipment_status))
                except Exception as e:
                    print(f"ERROR handling {invoice.id}: {str(e)}")
                    errored.append((invoice.id, new_shipment_status))
            else:
                print("no update needed", invoice.shipment_status)

        return updated, errored

    def handle_update(self, invoice: Invoice, new_status: str):
        error = ""
        if new_status == "DELIVERED":
            print('disbursal manager notified')
            self.trigger_disbursal(invoice)
        elif new_status == "PAID_BACK":
            print('invoice marked as repaid')
        elif new_status == "DEFAULTED":
            print('handle default')
        else:
            error += f"unprocessed invoice status {new_status} for order {invoice.order_ref}\n"

    def mark_as_paid(self, order_id: str):
        # mark as paid and reduce
        pass

    def trigger_disbursal(self, invoice: Invoice):
        # ============== get loan terms ==========
        # calculate repayment info
        # TODO get actual invoice start date
        start_date = dt.datetime.utcnow()
        terms = invoice_to_terms(invoice.id, invoice.order_ref, invoice.value, start_date)
        self.update_invoice_with_loan_terms(invoice, terms)
        supplier = self.session.query(Supplier).filter(Supplier.supplier_id==invoice.supplier_id).first()
        msg = terms_to_email_body(terms, supplier.name if supplier else "TODO")

        # ================= send email to Tusker with FundRequest
        try:
            ec = EmailClient()
            ec.send_email(body=msg, subject="Arboreum Disbursal Request", targets=[DISBURSAL_EMAIL, ARBOREUM_DISBURSAL_EMAIL])
            invoice.finance_status = "DISBURSAL_REQUESTED"
            self.session.commit()
        except Exception as e:
            invoice.finance_status = "ERROR_SENDING_REQUEST"
            self.session.commit()
            raise AssertionError(f"Could not send email: {str(e)}") # TODO add custom exception


    def check_credit_limit(self, raw_order):
        target_location_id=raw_order.get('rcvr').get('id')
        supplier_id=raw_order.get('cust').get('id')
        purchaser_id = whitelist_service.get_whitelisted_purchaser_from_location_id(supplier_id, target_location_id)

        value=raw_order_to_price(raw_order)
        credit = self.get_credit_line_info(supplier_id)

        if credit[purchaser_id].available < value:
            raise CreditLimitException(
                f"Not enough Credit available {credit[purchaser_id].available} to fund invoice of value {value}"
            )

        return True

    # TODO turn this into a view using
    # https://stackoverflow.com/questions/9766940/how-to-create-an-sql-view-with-sqlalchemy
    def get_credit_line_info(self, supplier_id: str):
        credit_line_breakdown = {}
        for w_entry in whitelist_service.get_whitelist(supplier_id):
            credit_line_size  = w_entry.creditline_size if w_entry.creditline_size != 0 else 0

            invoices = self.session.query(Invoice).filter(Invoice.purchaser_id == w_entry.purchaser_id).all()
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

    def get_credit_line_summary(self, supplier_id: str, supplier_name: str):
        summary = CreditLineInfo(info=PurchaserInfo(name=supplier_name), supplier_id="tusker")
        credit_line_breakdown = self.get_credit_line_info(supplier_id)
        for c in credit_line_breakdown.values():
            summary.total += c.total
            summary.available += c.available
            summary.used += c.used
            summary.requested += c.requested
            summary.invoices += c.invoices
        return summary

    def get_provider_summary(self, provider: str):
        """ create a credit line summary for all customers whose role is user """
        credit = {}
        for supplier in self.session.query(Supplier).all():
            credit[supplier.name] = invoice_service.get_credit_line_summary(supplier_id=supplier.supplier_id, supplier_name=supplier.name)
        return credit



invoice_service = InvoiceService()


