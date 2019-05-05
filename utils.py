from enlighten import Counter
from operator import add as default_add, ge as default_ge, le as default_le
from toolz.curried import flip, curry, partial
from pprint import pformat
import log
import inspect
from gevent.pool import Pool
from gevent import monkey
from constants import ATP_PREFIX

monkey.patch_all


__all__ = [
    "str_split",
    "str_startswith",
    "str_strip",
    "add",
    "str_find",
    "ge",
    "le",
    "str_replace",
    "track_lacked",
    "log_exception",
    "run_in_pool",
    "resolve_url",
]

str_split = flip(str.split)
str_startswith = flip(str.startswith)
str_strip = flip(str.strip)
str_find = flip(str.find)
add = curry(default_add)
ge = curry(default_ge)
le = curry(default_le)


def str_replace(before, after):
    return lambda s: str.replace(s, before, after)


def track_lacked(key, url, data):
    lack_keys = [
        key
        for key, value in data.items()
        if not value and key not in ["seed", "code", "url"]
    ]
    if not lack_keys:
        return

    called_function = str(inspect.stack()[1][3])

    log.warning(
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
            log.error(
                "{} was called with {}, {}. {}".format(
                    fn.__name__, args, kwargs, str(e)
                )
            )

    return wrapper


def run_in_pool(fn, iterable, desc="", pool_size=5):
    items = list(iterable)
    progress = Counter(total=len(items), desc=desc)

    def run(fn, item):
        fn(item)
        progress.update()

    pool = Pool(pool_size)

    list(pool.imap(fn, items))


def resolve_url(url):
    if url and url != "#":
        return ATP_PREFIX + url

    return None
