from datetime import datetime
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Table, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import  create_engine


Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoice"

    id = Column(String(50), primary_key=True)
    order_ref = Column(String(50), nullable=False)
    supplier_id = Column(String(50), nullable=False) # on the order its called customer_id
    purchaser_id = Column(String(50), nullable=False)

    shipment_status = Column(String(50), nullable=True)
    finance_status = Column(String(50), nullable=True)

    financed_on = Column(DateTime, nullable=True)
    apr = Column(Float, nullable=True)
    # repaid = Column(Float, nullable=True)
    tenor_in_days=Column(Integer, nullable=True)

    data = Column(Text, nullable=False)
    value = Column(Float, nullable=True)

    payment_details = Column(Text, nullable=True)

    # delivery_date = Column(DateTime)

    created_on = Column(DateTime, default=datetime.now())
    # updated_on = Column(DateTime)

class Whitelist(Base):
    """ keeps track of the receivers whose invoices can be financed for each customer """
    __tablename__ = "whitelist"
    supplier_id = Column(String(50), primary_key=True)
    purchaser_id = Column(String(50), primary_key=True)
    location_id = Column(String(50), nullable=False, index=True) # NOTE: tuskers order will use this in the receiver.id field
    name = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    creditline_size = Column(Integer, nullable=False)
    apr = Column(Float, nullable=True)
    tenor_in_days=Column(Integer, nullable=True)


class User(Base): #TUSKER
    """ used to look up usernames and their passwords and their associated customer id """
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(50), primary_key=True, unique=True)
    username = Column(String(50), nullable=False)
    hashed_password = Column(String(64), nullable=False)
    role = Column(String(50), nullable=False)


class Supplier(Base):
    __tablename__ = "supplier"
    supplier_id = Column(String(50), primary_key=True) # matches customer_id in tuskers system 
    name = Column(String(50), nullable=False)
    creditline_size = Column(Integer, nullable=False)
    default_apr = Column(Float, nullable=True)
    default_tenor_in_days=Column(Integer, nullable=True)



 



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
