import uvicorn
from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware.middlewares import add_middlewares
from fastapi.responses import JSONResponse
from app.conf import F5TelemetryConfig
from app.core.agent import Agent
import logging
import os

from app.core import tasks
from app.api.routes import router as api_router
from app.core.notifiers import set_agent_for_notifiers


app_settings = F5TelemetryConfig.get_settings()
log = logging.getLogger(app_settings.app_name)

app = None

def bootstrap():
    global app
    if app:
        return app
    # REST API Settings
    app = FastAPI(title = app_settings.app_name,
                  description = app_settings.app_description,
                  version = app_settings.app_version,
                  debug = app_settings.app_debug)
    
    # Middleware Settings
    add_middlewares(app)
    """
    app.add_middleware(
        CORSMiddleware, allow_origins="*", allow_credentials = True,
        allow_methods=["*"], allow_headers=["*"],
    )
    """

    app.add_event_handler("startup", tasks.create_start_app_handler(app))
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))
    
    # Routes
    app.include_router(api_router, prefix = app_settings.app_api_vers_path, tags=["api"])

    # Initialize agents
    agent = Agent.instance()
    agent.initialize_agent_module()
    agent.launch_agent()

    set_agent_for_notifiers(agent)
    
    return app

if not app:
    app = bootstrap()


def start():
    print("Running REST API/Prometheus metrics server")
    uvicorn.run(app, host=app_settings.app_ipaddr,
        port = app_settings.app_ipport,
        log_level = app_settings.app_debug)
    
if __name__ == "__main__":
    start()
