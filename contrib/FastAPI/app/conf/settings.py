"""
   STATIC and SECRET data
"""
from pydantic import (
    BaseModel,
    BaseSettings,
    PyObject,
    PostgresDsn,
    Field,
)
from dotenv import load_dotenv
from .apptypes import enumclass
from app.conf.singleton import Singleton
import os


"""
*********************
 CONFIG STRUCTURES
*********************
"""

"""
   nginx controllers could be of various types - internal to F5 or external
   These are data sources that the app proxies and massages info before
   delivering back to the client.
   Assuming only one controller to be active at a time
"""

class nc_mode(enumclass):
    NGINX_CONTROLLER        = 'nc'
    NGINX_INSTANCE_MANAGER  = 'nim'
    NGINX_MANAGEMENT_SYSTEM = 'nms'
    BIG_IQ                  = 'bigiq'


class nc_settings(BaseModel):
    nc_mode: nc_mode = None
    nc_name: str     = None
    nc_fqdn: str     = None
    nc_username: str = None
    nc_password: str = None

class db_settings(BaseModel):
    db_server: str   = None
    db_username: str = None
    db_password: str = None
    db_db: str       = None
    db_method: str   = None
    db_port: int     = None
    db_uri: str      = None


class app_env(enumclass):
    APP_ENV_DEV  = "development"
    APP_ENV_PROD = "production"
    APP_ENV_TEST = "testing"


class app_settings(BaseModel):
    app_name:          str            = None
    app_version:       str            = None
    app_api_vers_path: str            = None
    app_description:   str            = None
    app_nc_config:     nc_settings    = None
    app_db_config:     db_settings    = None
    app_ipaddr:        str            = None
    app_ipport:        int            = None
    app_loglevel:      int            = None
    app_debug:         int            = None
    app_env:           app_env        = None
    app_mode:          str            = None

    class Config:
        env_file = ".env"


class UniqueF5Telemetry(Singleton):
    def get_settings(self):
        return self.instance().get_settings()


@UniqueF5Telemetry
class F5TelemetryConfig(BaseSettings):
    app_settings = app_settings

    def __init__(self):

        # Load the environment variables
        if os.getenv('APP_ENV') != "testing":
            # app_settings = test_settings
            # return
            load_dotenv()
    
        # Source them into app-context
        app_settings.app_version        = "0.1.0"
        app_settings.app_name           = "F5-Telemetry"
        app_settings.app_description    = "F5-Telemetry Tracking"
        app_settings.app_api_vers_path  = "/api/v1"
        app_settings.app_env            = os.getenv('APP_ENV')
        app_settings.app_debug          = os.getenv('APP_DEBUG')
        app_settings.app_ipaddr         = os.getenv('APP_IPADDR')
        app_settings.app_ipport         = int(os.getenv('APP_PORT'))
        app_settings.app_mode           = os.getenv('APP_MODE')
        proxy                           = os.getenv('NGINX_PROXY_MODE')
        self.switch_ncmode(proxy)
        app_db_config = db_settings()
        app_db_config.db_server   = os.getenv('POSTGRES_SERVER')
        app_db_config.db_username = os.getenv('POSTGRES_USERNAME')
        app_db_config.db_password = os.getenv('POSTGRES_PASSWORD')
        app_db_config.db_db       = os.getenv('POSTGRES_DB')
        app_db_config.db_method   = os.getenv('POSTGRES_METHOD')
        app_db_config.db_port     = os.getenv('POSTGRES_PORT')
        if app_db_config.db_server == ":memory:":
            app_db_config.db_uri = (
                f"{app_db_config.db_method}:///{app_db_config.db_server}"
            )
        else:
            app_db_config.db_uri = (
                f"{app_db_config.db_method}://{app_db_config.db_username}"
                f":{app_db_config.db_password}@{app_db_config.db_server}:"
                f"{app_db_config.db_port}/{app_db_config.db_db}",
            )
        app_settings.app_db_config = app_db_config
        if app_settings.app_nc_config.nc_mode is None:
            raise ValueError('app is not configured. Environment file is missing\n')  

    def switch_ncmode(self, proxy):
        app_nc_config = nc_settings()
        app_nc_config.nc_mode    = proxy
        app_nc_config.nc_name    = os.getenv(f'NGINX_CONTROLLER_TYPE_{proxy}')
        app_nc_config.nc_fqdn    = os.getenv(f'NGINX_CONTROLLER_FQDN_{proxy}')
        app_nc_config.nc_username = os.getenv(f'NGINX_CONTROLLER_USERNAME_{proxy}')
        app_nc_config.nc_password = os.getenv(f'NGINX_CONTROLLER_PASSWORD_{proxy}')
        app_settings.app_nc_config = app_nc_config

    def set_ncmode(self, _nc_mode):
        if app_settings.app_nc_config.nc_mode.has_value(_nc_mode):
            app_settings.app_nc_config._nc_mode = _nc_mode
            self.switch_ncmode(self, _nc_mode)
        else:
            raise("{_nc_mode} is invalid for the app")


    def get_settings(self):
        """
           return the app-config settings
        """
        return self.app_settings
