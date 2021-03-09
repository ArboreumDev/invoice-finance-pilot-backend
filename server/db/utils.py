from db.database import session
from db.models import Invoice


def get_invoices():
    result = session.query(Invoice).all()
    print('allinvoices', result)

    return result
