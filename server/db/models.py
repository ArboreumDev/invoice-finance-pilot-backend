from sqlalchemy import Table

from db.database import metadata, engine

# Tables, auto map
# ShipmentStatusMap = Table("shipment_status_map", metadata, autoload=True, autoload_with=engine)
# FinanceStausMap = Table("finance_status_map", metadata, autoload=True, autoload_with=engine)
Invoice = Table("invoice", metadata, autoload=True, autoload_with=engine)
