from fastapi.middleware.cors import CORSMiddleware
from app.conf.settings import F5TelemetryConfig

from prometheusrock import PrometheusMiddleware, metrics_route

origins = [
    "https://mydomain.com",
    "http://myserver.amazonaws:6000",
]

def add_middlewares(app):
    app_settings = F5TelemetryConfig.get_settings()

    # Add CORS
    app.add_middleware(CORSMiddleware,
        allow_origins=origins, allow_credentials = True,
        allow_methods=["GET", "POST"], # allow_headers=["*"],
    )

    # Add Prometheus
    app.add_middleware(PrometheusMiddleware)
    app_root = F5TelemetryConfig.get_settings().app_api_vers_path
    app.add_route(app_root + "/metrics", metrics_route)

