from datetime import datetime

from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Table)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


from db.database import engine, metadata

# Tables, auto map
# ShipmentStatusMap = Table("shipment_status_map", metadata, autoload=True, autoload_with=engine)
# FinanceStausMap = Table("finance_status_map", metadata, autoload=True, autoload_with=engine)
InvoiceTable = Table("invoice", metadata, autoload=True, autoload_with=engine)


class Invoice(Base):
    __tablename__ = "invoice"

    id = Column(Integer, primary_key=True)

    shipment_status = Column(Integer, ForeignKey("shipment_status_map.id"), nullable=False)
    finance_status = Column(Integer, ForeignKey("finance_status_map.id"), nullable=True)

    cost = Column(Float)
    delivery_date = Column(DateTime)
    source_id = Column(String)

    # data = Column(Text)

    created_on = Column(DateTime, default=datetime.now())
    updated_on = Column(DateTime)


#############################
# Constants
#############################
class ShipmentStatusMap(Base):
    __tablename__ = "shipment_status_map"

    id = Column(Integer, primary_key=True)
    status = Column(String, unique=True)


class FinanceStausMap(Base):
    __tablename__ = "finance_status_map"

    id = Column(Integer, primary_key=True)
    status = Column(String, unique=True)
