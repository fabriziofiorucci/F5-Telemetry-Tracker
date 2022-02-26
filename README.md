# F5 Telemetry Tracker

## Description

This tool helps tracking NGINX Plus instances managed by NGINX Controller and NGINX Instance Manager, and TMOS (BIG-IP, VIPRION, VE) instances managed by BIG-IQ

It has been tested against:

- NGINX Controller 3.18, 3.18.2, apim-3.19.2
- NGINX Instance Manager 1.0.1, 1.0.2, 1.0.3, 1.0.4, 2.0, 2.0.1
- BIG-IQ 8.1.0, 8.1.0.2

Communication to NGINX Controller / NGINX Instance Manager / BIG-IQ is based on REST API, current features are:

- REST API mode
  - `/instances` and `/f5tt/instances` - return JSON output - If the request includes the `Accept-Encoding: gzip` header the response will be compressed
  - `/metrics` and `/f5tt/metrics` - return Prometheus compliant output
- High level reporting
  - `/reporting/xls` and `/f5tt/reporting/xls` - return a reporting spreadsheet in xls format (currently supported for BIG-IQ, when running as native python code and docker image only)
- JSON Telemetry mode
  - POSTs instance statistics to a user-defined HTTP(S) URL (STATS_PUSH_MODE: CUSTOM)
  - Basic authentication support
  - Configurable push interval (in seconds)
- Grafana visualization mode
  - Pushes instance statistics to pushgateway (STATS_PUSH_MODE: PUSHGATEWAY)
- Automated e-mail reporting
  - Sends an email containing the report JSON file as an attachment named nginx_report.json for NGINX Instance Manager and NGINX Controller, and bigip_report.json for BIG-IQ
  - Support for plaintext SMTP, STARTTLS, SMTP over TLS, SMTP authentication, custom SMTP port
  - Configurable push interval (in days)
- HTTP(S) proxy support
- CVE tracking
- Resource and applications telemetry (currently supported for BIG-IQ, when running as native python code and docker image only)

## Additional tools

Additional tools can be found [here](/contrib)

- [BIG-IQ Collector](/contrib/bigiq-collect) - Offline BIG-IQ inventory processing
- [F5TT on BIG-IQ Docker](/contrib/bigiq-docker) - Run F5TT onboard BIG-IQ CM virtual machine
- [Report Generator](/contrib/report-generator) - Offline report generator
- [Grafana](/contrib/grafana) - Sample Grafana dashboards
- [FastAPI](/contrib/FastAPI) - FastAPI backend with integrated agent

## Deployment modes

JSON telemetry mode

```mermaid
sequenceDiagram
    participant Control Plane
    participant F5 Telemetry Tracker
    participant Third party collector
    participant REST API client
    participant Email server

    loop Telemetry aggregation
      F5 Telemetry Tracker->>Control Plane: REST API polling
      F5 Telemetry Tracker->>F5 Telemetry Tracker: Raw data aggregation
    end
    F5 Telemetry Tracker->>Third party collector: Push JSON reporting data
    REST API client->>F5 Telemetry Tracker: Fetch JSON reporting data
    F5 Telemetry Tracker->>Email server: Email with attached JSON reporting data
```

Grafana visualization mode

```mermaid
sequenceDiagram
    participant Control Plane
    participant F5 Telemetry Tracker
    participant Pushgateway
    participant Prometheus
    participant Grafana

    loop Telemetry aggregation
      F5 Telemetry Tracker->>Control Plane: REST API polling
      F5 Telemetry Tracker->>F5 Telemetry Tracker: Raw data aggregation
    end
    F5 Telemetry Tracker->>Pushgateway: Push telemetry
    Prometheus->>Pushgateway: Scrape telemetry
    Grafana->>Prometheus: Visualization
```

## Prerequisites

- Kubernetes or Openshift cluster
- Private registry to push the F5 Telemetry Tracker image
- One of:
  - NGINX Controller 3.18, 3.18.2, apim-3.19.2
  - NGINX Instance Manager 1.0.1, 1.0.2, 1.0.3, 1.0.4, 2.0, 2.0.1
  - BIG-IQ 8.1.0, 8.1.0.2
- SMTP server if automated email reporting is used
- NIST NVD REST API Key for full CVE tracking (https://nvd.nist.gov/developers/request-an-api-key)

# How to build and run

## For Kubernetes/Openshift

The F5 Telemetry Tracker image is available on Docker Hub as:

```
fiorucci/f5-telemetry-tracker:latest
```

The 1.f5tt.yaml file references that by default.

If you need to build and push NGINX your own image to a private registry:

```
git clone fabriziofiorucci/F5-Telemetry-Tracker
cd F5-Telemetry-Tracker/f5tt

docker build --no-cache -t PRIVATE_REGISTRY:PORT/f5-telemetry-tracker:latest .
docker push PRIVATE_REGISTRY:PORT/f5-telemetry-tracker:latest
```

## As a native python application

F5 Telemetry Tracker requires:

- Any Linux distribution
- Python 3 (tested on 3.9+)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Requests](https://docs.python-requests.org/en/master/)
- [XLSX Writer](https://pypi.org/project/XlsxWriter/)
- [Pandas](https://pandas.pydata.org/)

f5tt/f5tt.sh is a sample script to run F5 Telemetry Tracker from bash

## Additional modes of operation

See the [contrib section](/contrib/)

- [BIG-IQ Collector](/contrib/bigiq-collect) - Offline BIG-IQ inventory processing
- [F5TT on BIG-IQ Docker](/contrib/bigiq-docker) - Run F5TT onboard BIG-IQ CM virtual machine
- [Report Generator](/contrib/report-generator) - Offline report generator
- [Grafana](/contrib/grafana) - Sample Grafana dashboard
- [FastAPI](/contrib/FastAPI) - FastAPI backend with integrated agent

# How to deploy

## For Kubernetes/Openshift

```
cd F5-Telemetry-Tracker/manifests
```

Edit `1.f5tt.yaml` to customize:

- image name:
  - To be set to your private registry image (only if not using the image available on Docker Hub)
- environment variables:

| Variable  | Description |
| ------------- |-------------|
| F5TT_ADDRESS | optional IP address F5 Telemetry Tracker should listen on. Default is 0.0.0.0 |
| F5TT_PORT| optional TCP port F5 Telemetry Tracker should listen on. Default is 5000
| HTTP_PROXY| to be set if HTTP proxy must be used to connect to NGINX Controller, NGINX Instance Manager or BIG-IQ
| HTTPS_PROXY| to be set if HTTPS proxy must be used to connect to NGINX Controller, NGINX Instance Manager or BIG-IQ
| NIST_API_KEY| API Key for full NIST NVD CVE tracking (get your key at https://nvd.nist.gov/developers/request-an-api-key)
| DATAPLANE_TYPE| can be NGINX_CONTROLLER, NGINX_INSTANCE_MANAGER (NIM 1.x), NGINX_MANAGEMENT_SYSTEM (NIM 2.x) or BIG_IQ
| DATAPLANE_FQDN| the FQDN of your NGINX Controller / NGINX Instance Manager 1.x-2.x / BIG-IQ instance| format must be http[s]://FQDN:port
| DATAPLANE_USERNAME| the username for authentication
| DATAPLANE_PASSWORD| the password for authentication
| STATS_PUSH_ENABLE | if set to "true" push mode is enabled, disabled if set to "false" |
| STATS_PUSH_MODE | either CUSTOM or PUSHGATEWAY, to push (HTTP POST) JSON to custom URL and to push metrics to pushgateway, respectively |
| STATS_PUSH_URL | the URL where to push statistics |
| STATS_PUSH_INTERVAL | the interval in seconds between two consecutive push |
| STATS_PUSH_USERNAME | (optional) the username for POST Basic Authentication |
| STATS_PUSH_PASSWORD | (optional) the password for POST Basic Authentication |
| EMAIL_ENABLED | if set to "true" automated email reporting is enabled, disabled if set to "false" |
| EMAIL_INTERVAL| the interval in days between two consecutive email reports |
| EMAIL_SERVER | the FQDN of the SMTP server to use |
| EMAIL_SERVER_PORT| the SMTP server port |
| EMAIL_SERVER_TYPE| either "plaintext", "starttls" or "ssl" |
| EMAIL_AUTH_USER| optional, the username for SMTP authentication |
| EMAIL_AUTH_PASS| optional, the password for SMTP authentication |
| EMAIL_SENDER| the sender email address |
| EMAIL_RECIPIENT| the recipient email address |

- Ingress host:
  - By default it is set to `f5tt.ff.lan`

For standalone operations (ie. REST API + optional push to custom URL):

```
kubectl apply -f 0.ns.yaml
kubectl apply -f 1.f5tt.yaml
```

To push statistics to pushgateway also apply:

```
kubectl apply -f 2.prometheus.yaml
kubectl apply -f 3.grafana.yaml
kubectl apply -f 4.pushgateway.yaml
```

By default `2.prometheus.yaml` is configured for push mode, it must be edited decommenting the relevant section for pull mode

To setup visualization:

- Grafana shall be configured with a Prometheus datasource using by default http://prometheus.f5tt.ff.lan
- Import the `contrib/grafana/F5-Telemetry-Tracker.json` sample dashboard in Grafana

Service names created by default as Ingress resources are:

- `f5tt.ff.lan` - REST API and Prometheus scraping endpoint
- `pushgateway.f5tt.ff.lan` - Pushgateway web GUI
- `prometheus.f5tt.ff.lan` - Prometheus web GUI
- `grafana.f5tt.ff.lan` - Grafana visualization web GUI

## As a native python application

Edit `f5tt/f5tt.sh` and run it

## Using F5 Support solutions

See F5 Support solutions:

- K83394355: How to count the number of NGINX instances with F5 Telemetry Tracker on NGINX Instance Manager - https://support.f5.com/csp/article/K83394355
- K45028541: How to count the number of NGINX instances with F5 Telemetry Tracker on NGINX Controller - https://support.f5.com/csp/article/K45028541
- K29144504: How to install and use (Offline) F5 Telemetry collection Script on BIG-IQ - https://support.f5.com/csp/article/K29144504

# Usage

See the [usage page](/USAGE.md)
