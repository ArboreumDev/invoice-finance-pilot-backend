# from: https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook
import logging
from logging import config

config.fileConfig("./logging.conf", disable_existing_loggers=False)


def get_logger(name):
    return logging.getLogger(name)
