import os
from typing import Generator

from airtable.airtable_service import AirtableService
from database.db import SessionLocal
from dotenv import load_dotenv
from fastapi import Request
from utils.logger import get_logger

load_dotenv()
api_key = os.getenv("AIRTABLE_API_SECRET")
base_id = os.getenv("AIRTABLE_BASE_ID")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_air() -> Generator:
    yield AirtableService(api_key, base_id)


def log_request(request: Request):
    logger = get_logger("api")
    logger.info(f"{request.method} {request.url}")

    logger.debug("Params:")
    for name, value in request.path_params.items():
        logger.debug(f"\t{name}: {value}")

    if hasattr(request, "_json"):
        logger.debug("Body:")
        try: 
            for name, value in request._json.items():
                logger.debug(f"\t{name}: {value}")
        except:
            print("error logging body", request._json)

    logger.debug("Headers:")
    for name, value in request.headers.items():
        logger.debug(f"\t{name}: {value}")
