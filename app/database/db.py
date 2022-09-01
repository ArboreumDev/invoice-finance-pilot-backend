from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from database.const import TEST_DB_URL, PROD_DB_URL
import os
from dotenv import load_dotenv

# engine = create_engine(TEST_DB_URL, echo=True)
load_dotenv()
env = os.getenv("ENVIRONMENT")
db_url = PROD_DB_URL if env == "PRODUCTION" else TEST_DB_URL
print("connecting to ", env , "-db")

# lets use this simple db for now TODO plug in our DB later
# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )


Base = declarative_base()

engine = create_engine(db_url, echo=False)
metadata = MetaData(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

