import log
import requests
from db import db

def request_html(url, from_cache=True):
    html = db.get(url)

    if not html or not from_cache:
        log.debug('Request {}'.format(url))
        response = requests.get(url)
        html = response.text
        db[url] = html

    return html

