from datetime import datetime
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Table, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import  create_engine


Base = declarative_base()

# from database.db import engine, metadata

# Tables, auto map
# ShipmentStatusMap = Table("shipment_status_map", metadata, autoload=True, autoload_with=engine)
# FinanceStausMap = Table("finance_status_map", metadata, autoload=True, autoload_with=engine)
# InvoiceTable = Table("invoice", metadata, autoload=True, autoload_with=engine)


class Invoice(Base):
    __tablename__ = "invoice"

    id = Column(String(50), primary_key=True)
    order_ref = Column(String(50), nullable=False)

    shipment_status = Column(String(50), nullable=True)
    finance_status = Column(String(50), nullable=True)
    # shipment_status = Column(Integer, ForeignKey("shipment_status_map.id"), nullable=False)
    # finance_status = Column(Integer, ForeignKey("finance_status_map.id"), nullable=True)

    data = Column(Text, nullable=False)
    value = Column(Float, nullable=True)

    # delivery_date = Column(DateTime)
    # source_id = Column(String)

    # created_on = Column(DateTime, default=datetime.now())
    # updated_on = Column(DateTime)


#############################
# Constants
#############################
# class ShipmentStatusMap(Base):
#     __tablename__ = "shipment_status_map"

#     id = Column(Integer, primary_key=True)
#     status = Column(String, unique=True)


# class FinanceStausMap(Base):
#     __tablename__ = "finance_status_map"

#     id = Column(Integer, primary_key=True)
#     status = Column(String, unique=True)
