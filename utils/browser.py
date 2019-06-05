from selenium import webdriver
from tbselenium.tbdriver import TorBrowserDriver
from multiprocessing import Queue

browser_connections = Queue()


def put_browser_back(browser):
    browser_connections.put(
        {
            "session_id": browser.session_id,
            "executor_url": browser.command_executor._url,
        }
    )


def get_browser():
    if browser_connections.empty():
        return TorBrowserDriver("/home/alex/tor-browser_en-US/")

    browser_connection = browser_connections.get()
    return get_remote_browser(**browser_connection)


def get_remote_browser(session_id, executor_url):
    from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

    # Save the original function, so we can revert our patch
    org_command_execute = RemoteWebDriver.execute

    def new_command_execute(self, command, params=None):
        if command == "newSession":
            # Mock the response
            return {"success": 0, "value": None, "sessionId": session_id}
        else:
            return org_command_execute(self, command, params)

    # Patch the function before creating the driver object
    RemoteWebDriver.execute = new_command_execute

    new_driver = webdriver.Remote(
        command_executor=executor_url, desired_capabilities={}
    )
    new_driver.session_id = session_id

    # Replace the patched function with original function
    RemoteWebDriver.execute = org_command_execute

    return new_driver


def close_browsers():
    while not browser_connections.empty():
        browser_connect = browser_connections.get()
        get_remote_browser(**browser_connect).quit()
