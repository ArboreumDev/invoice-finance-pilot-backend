import smtplib
from email.mime.text import MIMEText

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
        self.server.login(username, password)

    def send_email(self, body, subject, targets):
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(targets)
        self.server.sendmail(self.sender, targets, msg.as_string())


def terms_to_email_body(terms: LoanTerms):
    msg = f"""
    Hello Tusker,
    Gurugrupa has request to finance invoice {terms.invoice_id}
    agreed terms: {MONTHLY_INTEREST}
    {terms} TODO format this properly

    """
    return msg
