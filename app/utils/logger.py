# from: https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook
import logging
import os
from logging import config

# This line is to make the config file accessible regardless of the path that python is called from, we are now using
# a path relative to the current file
config.fileConfig(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logging.conf"),
    disable_existing_loggers=False,
)


def get_logger(name):
    return logging.getLogger(name)
