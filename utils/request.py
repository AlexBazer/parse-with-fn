import log
from db import db
from .browser import get_browser, put_browser_back


def request_html(url, from_cache=True):
    html = db.get(url)

    if not html or not from_cache:
        log.debug("Request {}".format(url))
        browser = get_browser()
        browser.get(url)
        html = browser.page_source
        put_browser_back(browser)
        db.set(url, html)

    return html
