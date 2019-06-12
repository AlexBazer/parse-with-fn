from tbselenium.tbdriver import TorBrowserDriver
from huey import RedisHuey

huey = RedisHuey('browser')

browser = None

def get_browser():
    return TorBrowserDriver("/home/alex/tor-browser_en-US/")

@huey.on_startup()
def create_browser():
    global browser
    browser = get_browser()

@huey.task()
def get_html(url):
    browser.get(url)
    return browser.page_source
