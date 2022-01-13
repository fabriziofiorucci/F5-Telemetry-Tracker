# F5 Telemetry Tracker - Portable image for Linux

Portable images have been built using [Nuitka](https://nuitka.net/) and can be downloaded from the [releases page](https://github.com/fabriziofiorucci/NGINX-InstanceCounter/releases)

Supported control planes:

 -  NGINX Controller 3.18, 3.18.2, apim-3.19.2
 -  NGINX Instance Manager 1.0.1, 1.0.2, 1.0.3, 1.0.4, 2.0
 -  BIG-IQ 8.1.0, 8.1.0.2

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

- Rename `app.bin` to `NGINX-InstanceCounter.AppImage` and move it to /portable/Linux

```
mv app.bin ../Linux/NGINX-InstanceCounter.AppImage
```

- Edit and use the provided `nicstart.sh` script to run the generated image
- When the F5 Telemetry Tracker has started, it can be queried sending GET requests to:
  - http://127.0.0.1:5000/instances or http://127.0.0.1:5000/counter/instances for JSON reporting.
  - http://127.0.0.1:5000/metrics or http://127.0.0.1:5000/counter/metrics for Prometheus metrics
- Port 5000 is used by default, it can be customized setting NIC_PORT in `nicstart.sh`
- For full NIST NVD CVE tracking, get a REST API key at https://nvd.nist.gov/developers/request-an-api-key and configure it in `nicstart.sh`
