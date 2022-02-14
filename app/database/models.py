from datetime import datetime
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Table, Text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import  create_engine
from sqlalchemy.orm import  relationship
from sqlalchemy.sql.sqltypes import Boolean
from database.db import Base


class Invoice(Base):
    __tablename__ = "invoice"

    id = Column(String(50), primary_key=True)
    order_ref = Column(String(50), nullable=False)
    # TODO add ForeignKey("users.user_id")
    supplier_id = Column(String(50), nullable=False) # on the order its called customer_id
    # TODO add ForeignKey("whitelist.purchaser_id")
    purchaser_id = Column(String(50), nullable=False)

    shipment_status = Column(String(50), nullable=True)
    finance_status = Column(String(50), nullable=True)
    verified = Column(Boolean, default=False)

    apr = Column(Float, nullable=True)
    # repaid = Column(Float, nullable=True)
    tenor_in_days=Column(Integer, nullable=True)

    data = Column(Text, nullable=False)
    value = Column(Float, nullable=True)

    payment_details = Column(Text, nullable=True)

    # delivery_date = Column(DateTime)

    delivered_on = Column(DateTime, nullable=True)
    financed_on = Column(DateTime, nullable=True)
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_on = Column(DateTime, default=datetime.now)

    # TODO (maybe) add relationships
    # supplier = relationship("Supplier", back_populates="invoices")


class Whitelist(Base):
    """ keeps track of the receivers whose invoices can be financed for each customer """
    __tablename__ = "whitelist"
    supplier_id = Column(String(50), primary_key=True)
    purchaser_id = Column(String(50), primary_key=True)
    # TODO move purchaser details to purchaser table
    location_id = Column(String(50), nullable=False, index=True) # NOTE: tuskers order will use this in the receiver.id field
    name = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    creditline_size = Column(Integer, nullable=False)
    apr = Column(Float, nullable=True)
    tenor_in_days = Column(Integer, nullable=True)


class Purchaser(Base):
    __tablename__ = "purchaser"
    purchaser_id = Column(String(50), primary_key=True)
    name = Column(String(50), nullable=False)
    credit_limit = Column(Integer, nullable=False)


class User(Base): #TUSKER
    """ used to look up usernames and their passwords """
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(50), primary_key=True, unique=True)
    username = Column(String(50), nullable=False, unique=True)
    hashed_password = Column(String(64), nullable=False)
    role = Column(String(50), nullable=False)


class Supplier(Base):
    __tablename__ = "supplier"
    supplier_id = Column(String(50), primary_key=True) # matches customer_id in tuskers system 
    creditline_id = Column(String(50), nullable=True) # used to interface with liquiloans ID
    name = Column(String(50), nullable=False)
    creditline_size = Column(Integer, nullable=False) # total credit line size
    default_apr = Column(Float, nullable=True)
    default_tenor_in_days=Column(Integer, nullable=True)
    data = Column(Text, nullable=True)

    # TODO add relatioship to invoices
    # invoices = relationship("Invoice", back_populates="supplier")
    

class KYCUser(Base):
    __tablename__ = "kycuser"
    phone_number = Column(String(50), primary_key=True) # matches customer_id in tuskers system 
    status = Column(String(50), nullable=True) # used to interface with liquiloans ID
    # data = Column(JSONB, nullable=False) # like this?
    data = Column(Text(), nullable=False)
 

 



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
