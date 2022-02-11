# F5-Telemetry/tests/conftest.py

import pytest
import os, signal
from fastapi.testclient import TestClient
from .conftest import AppServer, app_settings

app = AppServer()
client = TestClient(app.app_ctx)
client.base_url = "http://" + app_settings.app_ipaddr + ":" + str(app_settings.app_ipport)

# @pytest.fixture(scope="module")
def test_setup():
    app.start()


# @pytest.fixture()
def test_root():
    response = client.get('/')
    assert response.status_code == 404

def test_api_root():
    response = client.get('/api/v1')
    assert response.status_code == 200
    assert response.content == b'{"message":"Welcome to F5Telemetry"}'

def test_instance_root():
    response = client.get('/api/v1/instances')
    assert response.status_code == 200
    if app_settings.app_mode == "mock":
        assert 'subscription' in str(response.content)
        assert 'instances' in str(response.content)

def test_instance_root():
    response = client.get('/api/v1/counter/instances')
    assert response.status_code == 200
    if app_settings.app_mode == "mock":
        assert 'subscription' in str(response.content)
        assert 'instances' in str(response.content)

def test_metrics_root():
    response = client.get('/api/v1/counter/metrics')
    assert response.status_code == 200
    if app_settings.app_mode == "mock":
        assert 'subscription' in str(response.content)

def test_reporting_root():
    response = client.post('/api/v1/reporting/report1', json = {"report_type": "report1"})
    assert response.status_code == 200
    if app_settings.app_mode == "mock":
        assert 'subscription' in str(response.content)

def test_reporting_root():
    response = client.post('/api/v1/counter/reporting/report1', json = {"report_type": "report1"})
    assert response.status_code == 200
    if app_settings.app_mode == "mock":
        assert 'subscription' in str(response.content)

def test_prometheus_metrics():
    response = client.get('/api/v1/metrics')
    assert response.status_code == 200
    assert 'HELP' in str(response.content)
    assert 'TYPE' in str(response.content)

def test_terminate():
    os.kill(os.getpid(), signal.SIGINT)
    pytest.raises(Exception)
