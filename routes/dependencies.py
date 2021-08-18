import logging
from typing import Generator

from fastapi import Request

from database.db import SessionLocal
from utils.logger import get_logger


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def log_request(request: Request):
    logger = get_logger("api")
    logger.info(f"{request.method} {request.url}")
    logger.debug("Params:")
    for name, value in request.path_params.items():
        logger.debug(f"\t{name}: {value}")
    logger.debug("Headers:")
    for name, value in request.headers.items():
        logger.debug(f"\t{name}: {value}")
