from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from database.const import TEST_DB_URL

# DB_URI = "postgres://vqjhwxvzfhpwft:4741891ca218a2eafeccf5530b4db15abe9684a43884077b9ea2e4f1225493ff@ec2-54-89-49-242.compute-1.amazonaws.com:5432/d3e6s3pg9j6vq1"

# engine = create_engine(TEST_DB_URL, echo=True)
engine = create_engine(TEST_DB_URL, echo=False)
metadata = MetaData(engine)

Session = sessionmaker(bind=engine)
session = Session()
