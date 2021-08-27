from sqlalchemy.orm import Session


def reset_db(db: Session, deleteWhitelist=False):
    db.execute("TRUNCATE invoice, users, supplier")
    if deleteWhitelist:
        db.execute("TRUNCATE whitelist")