import os 
from dotenv import load_dotenv

load_dotenv()

# TODO get those from .env
# POSTGRES SETUP
TEST_DB_USER = os.getenv("TEST_DB_USER") #"MwJ59dpuQT4ypdnXt"
TEST_DB_HOST = "localhost"
TEST_DB_PORT = os.getenv("POSTGRES_TEST_PORT")
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD")
TEST_DB_NAME = "arboreum_backend_prod"
TEST_DB_URL = (
    f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
)

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
PROD_DB_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# SQLLITE
# TODO figure out how to give the same session to multiple threads
# TEST_DB_URL = 'sqlite:///test_invoice.db'
# TEST_DB_URL = 'sqlite:///test_invoice.db?check_same_thread=False'