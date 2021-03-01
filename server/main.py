from typing import Optional, Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum
import datetime
from humps import camelize

origins = [
    "http://localhost",
    "http://localhost:3000",
]

class ShipmentStatus(str, Enum):
    AWAITING_SHIPMENT = "AWAITING_SHIPMENT"
    SHIPPING = "SHIPPING"
    DELIVERED = "DELIVERED"

class FinanceStatus(str, Enum):
    NONE = "NONE"
    FINANCED = "FINANCED"
    REPAID = "REPAID"
    DEFAULTED = "DEFAULTED"


def to_camel(string):
    return camelize(string)

class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class Invoice(CamelModel):
    id: int
    amount: int
    destination: str
    shipping_status: ShipmentStatus = ShipmentStatus.AWAITING_SHIPMENT
    status: FinanceStatus = FinanceStatus.NONE


def init_invoices():
    _invoices = [
        {"id":1,"amount":1000,"destination":"Ramesh","shipping_status":"AWAITING_SHIPMENT"},
        {"id":2,"amount":1000,"destination":"Ajit","shipping_status":"AWAITING_SHIPMENT"},
        {"id":3,"amount":1000,"destination":"Pavan","shipping_status":"SHIPPING"}
    ]

    return {invoice['id']: Invoice(**invoice) for invoice in _invoices}


invoices = init_invoices()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/invoices", response_model=List[Invoice])
def get_invoices():
    return list(invoices.values())


@app.post("/invoice", response_model=Invoice)
def update_invoice(invoice: Invoice):
    invoices[invoice.id] = invoice
    return invoice


# @app.post("/email", response_model=TODO}