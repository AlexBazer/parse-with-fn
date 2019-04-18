import logging
import logzero
from logzero import logger

logzero.logfile('./runner.log', loglevel=logging.WARNING)

def debug(msg):
    logger.debug(msg)

def info(msg):
    logger.info(msg)

def warning(msg):
    logger.warning(msg)

def error(msg):
    logger.error(msg)
