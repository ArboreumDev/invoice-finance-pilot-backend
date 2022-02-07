from sqlalchemy.orm import Session
from typing import Dict
from fastapi.encoders import jsonable_encoder
import json


def reset_db(db: Session, tables=[]):
    if tables:
        db.execute("TRUNCATE " + ",".join(tables))
    else: 
        db.execute("TRUNCATE invoice, users, supplier, whitelist, purchaser")


def remove_none_entries(d: Dict):
    return {k:v for k,v in d.items() if v != None}

def serialize(obj):
    return json.dumps(jsonable_encoder(obj))

def deserialize(obj):
    return json.loads(jsonable_encoder(obj))
