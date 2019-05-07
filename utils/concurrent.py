from time import sleep
from uuid import uuid4
from multiprocessing import Process
from multiprocessing.pool import Pool

from toolz import curry
from progressbar import ProgressBar

from db import db

def run_in_pool(fn, iterable, desc="", pool_size=2):
    items = list(iterable)

    pool = Pool(pool_size)

    monitor_name = f"run_in_pool|{uuid4().hex}"
    monitor = Process(target=_monitor, args=(monitor_name, len(items), desc))

    fn = curry(_run, fn, monitor_name)
    monitor.start()

    try:
        result = list(pool.imap(fn, items))
        return result
    finally:
        db.delete(monitor_name)
        monitor.close()


def _monitor(fn_name, max_value, desc=""):
    progress = ProgressBar(max_value=max_value, prefix=desc)

    while True:
        progress.update(int(db.get(fn_name, raw=True) or 0))
        sleep(0.5)


def _run(fn, monitor_name, item):
    result = fn(item)
    db.incr(monitor_name)
    return result
