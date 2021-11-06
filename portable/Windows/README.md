# NGINX Instance Counter - Portable image for Windows

This portable image has been built using [Nuitka](https://nuitka.net/)

Steps to (re)build it:

- Setup nuitka on Windows: https://nuitka.net/doc/user-manual.html#tutorial-setup-and-build-on-windows
- install additional python packages

```
pip install flask
pip install requests
```

- Package the app.py script

```
python -m nuitka --onefile --mingw64 app.py
```

- Edit and use the provided nicstart.bat script to run the generated image

- Upon startup Windows will ask to allow traffic from the image to NGINX Instance Manager, NGINX Controller or BIG-IQ: all traffic is sent to NIM/NC/BIG-IQ management IP address and port (configurabile from nicstart.bat)

<img src="/images/portable-windows.1.jpg"/>

- When the NGINX Instance Counter has started, it can be queried sending a GET request to http://127.0.0.1:5000/instances or http://127.0.0.1:5000/counter/instances for JSON reporting. Prometheus metrics can be polled using http://127.0.0.1:5000/metrics or http://127.0.0.1:5000/counter/metrics

- Port 5000 is used by default, it can be customized setting NIC_PORT in nicstart.sh

<img src="/images/portable-windows.2.jpg"/>
