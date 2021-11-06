# NGINX Instance Counter - Portable image for Linux

This portable image has been built using [Nuitka](https://nuitka.net/)

Steps to (re)build it:

- Setup nuitka
- install additional python packages

```
pip install flask
pip install requests
```

- Package the app.py script

```
python3 -m nuitka --onefile app.py
```

- Edit and use the provided nicstart.sh script to run the generated image
- When the NGINX Instance Counter has started, it can be queried sending a GET request to http://127.0.0.1:5000/instances or http://127.0.0.1:5000/counter/instances for JSON reporting. Prometheus metrics can be polled using http://127.0.0.1:5000/metrics or http://127.0.0.1:5000/counter/metrics
- Port 5000 is used by default, it can be customized setting NIC_PORT in nicstart.sh
