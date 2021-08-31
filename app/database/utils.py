from sqlalchemy.orm import Session
from typing import Dict


def reset_db(db: Session, tables=[]):
    db.execute("TRUNCATE invoice, users, supplier, whitelist")
    if tables:
        db.execute("TRUNCATE " + ",".join(tables))


def remove_none_entries(d: Dict):
    return {k:v for k,v in d.items() if v != None}
