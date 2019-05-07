from .toolz import *
from .concurrent import run_in_pool
from constants import ATP_PREFIX

def resolve_url(url):
    if url and url != "#":
        return ATP_PREFIX + url

    return None
