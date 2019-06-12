import log
from urllib.parse import urlsplit, urlunsplit
from db import db
from .browser import get_html


def get_ajax_url(url):
    splitted = urlsplit(url)
    if 'ajax=true' in splitted.query:
        return url

    if splitted.query:
        splitted = splitted._replace(query=f"{splitted.query}&ajax=true")
    else:
        splitted = splitted._replace(query="ajax=true")

    return urlunsplit(splitted)

def request_html(url, from_cache=True):
    html = db.get(url)

    if not html or not from_cache:
        log.debug("Request {}".format(url))
        html = get_html(get_ajax_url(url)).get(blocking=True)
        db.set(url, html)

    return html
