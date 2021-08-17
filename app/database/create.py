# import os
from sqlalchemy import create_engine
from database.const import TEST_DB_URL, PROD_DB_URL
# from sqlalchemy.orm import sessionmaker
from database.models import Base

# run this module to create all tables afresh
# somehow it didnt work when there was a database there already, so I had to delete it
# and the create it afresh, 
# => TODO learn how to do migrations

# engine = create_engine(TEST_DB_URL, echo=True)

print ("Choose env: 1. production, 2. test")
env = int(input())
print('you chose: ', "production" if env==1 else "TEST")
db_url = PROD_DB_URL if env==1 else TEST_DB_URL



engine = create_engine(db_url, echo=True)
engine.connect()
# print(TEST_DB_URL)
# print(engine)

Base.metadata.create_all(engine)
