import os 
from dotenv import load_dotenv

# TODO get those from .env
# POSTGRES SETUP
TEST_DB_USER = "MwJ59dpuQT4ypdnXt"
TEST_DB_HOST = "localhost"
TEST_DB_PORT = 5433
TEST_DB_PASSWORD = "Fj01gToHm4uv4f1LpBdvZn1RSR8wOWuRTClxBkdw4VQGKm0"
TEST_DB_NAME = "arboreum_backend_test"
TEST_DB_URL = (
    f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
)

load_dotenv()
PROD_DB_USER = os.getenv("POSTGRES_USER")
PROD_DB_HOST = os.getenv("POSTGRES_HOST")
PROD_DB_PORT = os.getenv("POSTGRES_PORT")
PROD_DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PROD_DB_NAME = os.getenv("POSTGRES_DB")
PROD_DB_URL = (
    f"postgresql://{PROD_DB_USER}:{PROD_DB_PASSWORD}@{PROD_DB_HOST}:{PROD_DB_PORT}/{PROD_DB_NAME}"
)

# SQLLITE
# TODO figure out how to give the same session to multiple threads
# TEST_DB_URL = 'sqlite:///test_invoice.db'
# TEST_DB_URL = 'sqlite:///test_invoice.db?check_same_thread=False'