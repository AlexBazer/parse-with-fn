import inspect
from pprint import pformat
import logging
import logzero
from logzero import logger

logzero.logfile("./runner.log", loglevel=logging.WARNING)


def debug(msg):
    logger.debug(msg)


def info(msg):
    logger.info(msg)


def warning(msg):
    logger.warning(msg)


def error(msg):
    logger.error(msg)


def track_lacked(key, url, data):
    lack_keys = [
        key
        for key, value in data.items()
        if not value and key not in ["seed", "code", "url"]
    ]
    if not lack_keys:
        return

    called_function = str(inspect.stack()[1][3])

    warning(
        "{} | {}:{} lacks {} \n {}".format(
            called_function, key, url, lack_keys, pformat(data)
        )
    )


def log_exception(fn):
    def wrapper(*args, **kwargs):
        try:
            res = fn(*args, **kwargs)
            return res
        except Exception as e:
            error(
                "{} was called with {}, {}. {}".format(
                    fn.__name__, args, kwargs, str(e)
                )
            )

    return wrapper
