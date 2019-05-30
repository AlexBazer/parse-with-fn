import log
from urllib.parse import urlsplit, urlunsplit
from db import db
from .browser import get_browser, put_browser_back

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
        browser = get_browser()
        browser.get(get_ajax_url(url))
        html = browser.page_source
        put_browser_back(browser)
        db.set(url, html)

    return html
