# NGINX Instance Counter - Portable image for Linux

Portable images have been built using [Nuitka](https://nuitka.net/) and can be downloaded from the [releases page](/fabriziofiorucci/NGINX-InstanceCounter/releases)

Steps to (re)build:

- Setup nuitka
- install additional python packages

```
pip install flask
pip install requests
```

- Package the source files in `/portable/src`

```
python3 -m nuitka --onefile app.py
```

- Edit and use the provided `nicstart.sh` script to run the generated image
- When the NGINX Instance Counter has started, it can be queried sending GET requests to:
  - http://127.0.0.1:5000/instances or http://127.0.0.1:5000/counter/instances for JSON reporting.
  - http://127.0.0.1:5000/metrics or http://127.0.0.1:5000/counter/metrics for Prometheus metrics
- Port 5000 is used by default, it can be customized setting NIC_PORT in `nicstart.sh`
- For full NIST NVD CVE tracking, get a REST API key at https://nvd.nist.gov/developers/request-an-api-key and configure it in `nicstart.sh`
