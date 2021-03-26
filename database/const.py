# TODO get those from .env
TEST_DB_USER = "MwJ59dpuQT4ypdnXt"
TEST_DB_HOST = "localhost"
TEST_DB_PORT = 5433
TEST_DB_PASSWORD = "Fj01gToHm4uv4f1LpBdvZn1RSR8wOWuRTClxBkdw4VQGKm0"
TEST_DB_NAME = "arboreum_backend"

TEST_DB_URL = (
    f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
)

EXP_TEST_DB = 'sqlite:///invoice.db'