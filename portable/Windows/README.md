# F5 Telemetry Tracker - Portable image for Windows

Portable images have been built using [Nuitka](https://nuitka.net/) and can be downloaded from the [releases page](https://github.com/fabriziofiorucci/NGINX-InstanceCounter/releases)

Supported control planes:

 -  NGINX Controller 3.18, 3.18.2, apim-3.19.2
 -  NGINX Instance Manager 1.0.1, 1.0.2, 1.0.3, 1.0.4, 2.0
 -  BIG-IQ 8.1.0, 8.1.0.2

Steps to (re)build:

- Setup nuitka on Windows: https://nuitka.net/doc/user-manual.html#tutorial-setup-and-build-on-windows
- install additional python packages

```
pip install flask
pip install requests
pip install zstandard
```

- Package the source files in `/portable/src`

```
python -m nuitka --onefile --mingw64 app.py
```

- Rename `app.exe` to `NGINX-InstanceCounter.exe` and move it to /portable/Linux

- Edit and use the provided `nicstart.bat` script to run the generated image

- Upon startup Windows will ask to allow traffic from the image to NGINX Instance Manager, NGINX Controller or BIG-IQ: all traffic is sent to NIM/NC/BIG-IQ management IP address and port (configurabile from `nicstart.bat`)

<img src="/portable/Windows/images/portable-windows.1.jpg"/>

- When the F5 Telemetry Tracker has started, it can be queried sending a GET request to:
  - http://127.0.0.1:5000/instances or http://127.0.0.1:5000/counter/instances for JSON reporting.
  - http://127.0.0.1:5000/metrics or http://127.0.0.1:5000/counter/metrics for Prometheus metrics 

- Port 5000 is used by default, it can be customized setting NIC_PORT in `nicstart.bat`
- For full NIST NVD CVE tracking, get a REST API key at https://nvd.nist.gov/developers/request-an-api-key and configure it in `nicstart.bat`

<img src="/portable/Windows/images/portable-windows.2.jpg"/>
