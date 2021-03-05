from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker


DB_URI = "postgres://vqjhwxvzfhpwft:4741891ca218a2eafeccf5530b4db15abe9684a43884077b9ea2e4f1225493ff@ec2-54-89-49-242.compute-1.amazonaws.com:5432/d3e6s3pg9j6vq1"

# Engine
engine = create_engine(DB_URI, echo=False)

# Metadata
metadata = MetaData(engine)

# Session
Session = sessionmaker(bind=engine)
session = Session()
