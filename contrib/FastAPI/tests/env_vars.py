import os
import pytest

@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(args, early_config, parser):
    os.environ["APP_ENV"] = "testing"
    os.environ["APP_DEBUG"] = "debug"
    os.environ["APP_IPADDR"] = "localhost"
    os.environ["APP_PORT"] = '5000'
    os.environ["APP_MODE"] = 'mock'
    os.environ["NGINX_PROXY_MODE"] = "nc"

    os.environ["NGINX_CONTROLLER_TYPE"]='NGINX_CONTROLLER'
    os.environ["NGINX_CONTROLLER_FQDN"]="https://localhost:8888"
    os.environ["NGINX_CONTROLLER_USERNAME"]="username@domain"
    os.environ["NGINX_CONTROLLER_PASSWORD"]="thepassword"

    os.environ["NGINX_CONTROLLER_TYPE_nc"]='NGINX_CONTROLLER'
    os.environ["NGINX_CONTROLLER_FQDN_nc"]="https://localhost:8888"
    os.environ["NGINX_CONTROLLER_USERNAME_nc"]="username@domain"
    os.environ["NGINX_CONTROLLER_PASSWORD_nc"]="thepassword"

    os.environ["NGINX_CONTROLLER_TYPE_nim"]='NGINX_INSTANCE_MANAGER'
    os.environ["NGINX_CONTROLLER_FQDN_nim"]="https://localhost:8888"
    os.environ["NGINX_CONTROLLER_USERNAME_nim"]="username@domain"
    os.environ["NGINX_CONTROLLER_PASSWORD_nim"]="thepassword"

    os.environ["NGINX_CONTROLLER_TYPE_nms"]='NGINX_MANAGEMENT_SYSTEM'
    os.environ["NGINX_CONTROLLER_FQDN_nms"]="https://localhost:8888"
    os.environ["NGINX_CONTROLLER_USERNAME_nms"]="username@domain"
    os.environ["NGINX_CONTROLLER_PASSWORD_nms"]="thepassword"

    os.environ["NGINX_CONTROLLER_TYPE_bigiq"]='BIG_IQ'
    os.environ["NGINX_CONTROLLER_FQDN_bigiq"]="https://localhost:8888"
    os.environ["NGINX_CONTROLLER_USERNAME_bigiq"]="username@domain"
    os.environ["NGINX_CONTROLLER_PASSWORD_bigiq"]="thepassword"

    os.environ["POSTGRES_SERVER"]="localhost"
    os.environ["POSTGRES_USERNAME"]="postgres"
    os.environ["POSTGRES_PASSWORD"]="postgres"
    os.environ["POSTGRES_DB"]="test.db"
    os.environ["POSTGRES_PORT"]="5432"
    os.environ["POSTGRES_METHOD"]="postgresql+asyncpg"

    ##################
    # Agent Settings
    ##################
    # Notification Types
    os.environ['STATS_PUSH_ENABLE']="True"
    os.environ['EMAIL_ENABLED']="True"
    os.environ['INVENTORY_NOTIFY_TYPE']="True"
    
    # Proxy Settings
    os.environ['HTTP_PROXY']="True"
    os.environ['HTTPS_PROXY']="True"
    
    # CVE Tracking
    os.environ['NIST_API_KEY']="blah-blah-blah"
    # Push-mode notification Configuraitons
    # Push-notification types
    os.environ['STATS_PUSH_MODE']="True"
    os.environ['CUSTOM_PUSH_MODE']="False"
    os.environ['STATS_PUSH_INTERVAL']='30'
    os.environ['STATS_PUSH_URL']='stats.pushdomain.com'
    
    # Email-mode notification Configuraitons
    os.environ['EMAIL_ENABLED']="True"
    os.environ['EMAIL_INTERVAL']="60"
    os.environ['EMAIL_SENDER']='sender@example.com'
    os.environ['EMAIL_RECIPIENT']='receiver@bigiq.ff.com'
    os.environ['EMAIL_SERVER']='mail.ff.com'
    os.environ['EMAIL_SERVER_PORT']='25'
    os.environ['EMAIL_SERVER_TYPE']='imap'
    os.environ['EMAIL_AUTH_USER']="auth_user"
    os.environ['EMAIL_AUTH_PASS']="auth_pass"
