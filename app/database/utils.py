from sqlalchemy.orm import Session
from typing import Dict


def reset_db(db: Session, tables=[]):
    if tables:
        db.execute("TRUNCATE " + ",".join(tables))
    else: 
        db.execute("TRUNCATE invoice, users, supplier, whitelist")


def remove_none_entries(d: Dict):
    return {k:v for k,v in d.items() if v != None}
