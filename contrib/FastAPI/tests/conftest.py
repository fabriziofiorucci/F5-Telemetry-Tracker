from fastapi import FastAPI
from multiprocessing import Process
import time
import asynctest
import asyncio
import aiohttp
import uvicorn
from app.conf import F5TelemetryConfig
from app.api.main import bootstrap, app_settings


class App(asynctest.TestCase):
    """ Core application to test. """

    def __init__(self):

        # REST API Settings
        self.app = bootstrap()

    async def close(self):
        """ Gracefull shutdown. """
        logging.warning("Shutting down the app.")

class AppServer():
    def __init__(self):
        self.app_ctx = App().app
    def start(self):
        """ Startup server """
        self.proc = Process(target=uvicorn.run,
            name = app_settings.app_name,
            args=[self.app_ctx], kwargs = {
                    'host': app_settings.app_ipaddr,
                    'port': app_settings.app_ipport,
                    'log_level': app_settings.app_debug},
                    daemon = True)
        self.proc.start()
        time.sleep(0.2)  # time for server to start
                 

    async def tear_down(self):
        """ Shutdown the app """
        self.proc.terminate()
