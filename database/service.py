from database.db import session
import datetime as dt
from database.models import Invoice
from typing import Dict
from invoice.tusker_client import code_to_order_status, tusker_client
from utils.email import EmailClient, terms_to_email_body
import json
from utils.common import LoanTerms 
from utils.constant import DISBURSAL_EMAIL, MAX_CREDIT


def invoice_to_terms(id: str, amount: float, start_date: dt.datetime):
    return LoanTerms(
        invoice_id=id,
        principal=amount,
        interest=amount * 0.05,
        start_date=start_date,
        collection_date=start_date + dt.timedelta(days=90),
    )


class InvoiceService():
    def __init__(self):
        self.session = session
    
    def insert_new_invoice(self, raw_order: Dict):
        new_invoice = Invoice(
            id=raw_order.get("id"),
            order_ref=raw_order.get('ref_no'),
            shipment_status=code_to_order_status(raw_order.get('status')),
            finance_status="INITIAL",
            value=raw_order.get("prc", {}).get("pr_act", 0),
            # TODO maybe use pickle here? how are booleans preserved?
            data=json.dumps(raw_order)
        )
        self.session.add(new_invoice)
        self.session.commit()
        return new_invoice.id

    def update_invoice_shipment_status(self, invoice_id: str, new_status: str):
        invoice = self.session.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.shipment_status = new_status
        self.session.commit()

    def update_invoice_payment_status(self, invoice_id: str, new_status: str):
        invoice = self.session.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.finance_status = new_status
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
        invoices = {i.id: i for i in res}
        # get order_ref to track by
        all_reference_numbers = [i.order_ref for i in res]
        latest_raw_orders = tusker_client.track_orders(all_reference_numbers)
        print('updating ', len(latest_raw_orders), ' orders')
        # assert len(latest_raw_orders) == len(all_reference_numbers), "update missing"

        # compare with DB if status changed
        for order in latest_raw_orders[:1]:
            new_shipment_status = code_to_order_status(order.get("status"))
            invoice = invoices[order.get("id")]
            if new_shipment_status != invoice.shipment_status:
                # ...if new, enact consequence and if successful update DB
                print("old shipment status: ", invoice.shipment_status)
                print("new shipment status: ", new_shipment_status)
                try:
                    self.handle_update(invoice, new_shipment_status)
                    invoice.shipment_status = new_shipment_status
                    self.session.commit()
                    updated.append((invoice.id, new_shipment_status))
                except Exception as e:
                    print(f"ERROR handling {invoice.id}: {str(e)}")
                    errored.append((invoice.id, new_shipment_status))
            else:
                print("no update needed", invoice.shipment_status, new_shipment_status)

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
        msg = terms_to_email_body(invoice_to_terms(invoice.id, invoice.value, start_date))

        # ================= send email to Tusker with FundRequest
        try:
            ec = EmailClient()
            ec.send_email(body=msg, subject="Arboreum Disbursal Request", targets=[DISBURSAL_EMAIL])
            invoice.finance_status = "DISBURSAL_REQUESTED"
        except Exception as e:
            raise AssertionError(f"Could not send email: {str(e)}") # TODO add custom exception


    # TODO turn this into a view using
    # https://stackoverflow.com/questions/9766940/how-to-create-an-sql-view-with-sqlalchemy
    def free_credit(self):
        financed_invoices = self.session.query(Invoice).filter(Invoice.finance_status.in_(["DISBURSED", "DISBURSAL_REQUESTED"])).all()
        print('financed', financed_invoices)
        return MAX_CREDIT - sum([i.value for i in financed_invoices])
        # return 10000000

    def final_checks(self, raw_order):
        # verify doesnt cross credit limit
        # if not return custom error
        # verify customer / recipient is whitelisted
        # if not return custom error
        return True, "Ok"



invoice_service = InvoiceService()


