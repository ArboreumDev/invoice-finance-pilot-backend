import smtplib
from email.mime.text import MIMEText
from utils.common import LoanTerms


class EmailClient:
    def __init__(self):
        # TODO get this from .env
        smtp_ssl_host = "email-smtp.eu-west-2.amazonaws.com"
        smtp_ssl_port = 465
        username = "AKIA2AU4HUXQSXJSDCU7"
        password = "BLDEEAm/2Guhse+I9dZt2ZY60LU/DYl4EL1A/0lA22b7"
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
    {terms} TODO format this properly
    """
    return msg