import json
import smtplib
from email.mime.text import MIMEText

from database.models import Supplier
from utils.common import LoanTerms
from utils.constant import (EMAIL_HOST, EMAIL_PASSWORD, EMAIL_PORT,
                            EMAIL_USERNAME, MONTHLY_INTEREST)


class EmailClient:
    def __init__(self):
        # TODO get this from .env
        smtp_ssl_host = EMAIL_HOST
        smtp_ssl_port = EMAIL_PORT
        username = EMAIL_USERNAME
        password = EMAIL_PASSWORD
        if not EMAIL_USERNAME:
            raise NotImplementedError("missing secret")
        self.sender = "dev@arboreum.dev"
        self.server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
        # self.server.connect(EMAIL_HOST, EMAIL_PORT)
        # self.server.ehlo()
        # self.server.starttls()
        # self.server.ehlo()
        self.server.login(username, password)

    def send_email(self, body, subject, targets):
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(targets)
        # self.server.connect(EMAIL_HOST, EMAIL_PORT)
        # self.server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        self.server.sendmail(self.sender, targets, msg.as_string())


def terms_to_email_body(terms: LoanTerms, supplier: Supplier):
    msg = f"""
    Hello Tusker,\n
    {supplier.name} (creditlineId: {supplier.creditline_id}) has request to finance invoice {terms.invoice_id} from the
    order with reference number: {terms.order_id} \n
    to the following terms: \n
    {MONTHLY_INTEREST} percent monthly interest
    start: {terms.start_date.date()}
    principal: {terms.principal}
    interest: {terms.interest}
    total: {terms.principal + terms.interest}
    collection: {terms.collection_date.date()}

    Please \n
    1) create the loan on the liquiloans platform
    2) go to the AdminView Dashboard and
       2.1) change the status to FINANCED
       2.2) enter loanId
       2.3) hit 'change status'

    """
    return msg


def new_supplier_to_email_body(supplier: Supplier):
    msg = """
    Hello dear Loan Admin,\n\n
    A new supplier was registered. Please \n
    1) create a profile on Liquiloans,\n
    2) come back to the website and enter the creditlineId for the supplier\n\n

    Here is the Supplier Data:\n
    """
    for key, value in supplier.__dict__.items():
        if key != "data":
            msg += f"{key}: {value}\n"

    # add raw data to end of test
    msg += "\n============= RAW DATA FROM TUSKER ================== \n"
    try:
        for key, value in json.loads(supplier.data):
            msg += f"{key}: {value}\n"
    except Exception:
        msg += str(value)
    return msg
