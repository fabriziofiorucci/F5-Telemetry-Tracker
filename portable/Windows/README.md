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
python -m nuitka --follow-imports --onefile --mingw64 app.py
```

- Edit and use the provided nicstart.bat script to run the generated image

- Upon startup Windows will ask to allow traffic from the image to BIG-IQ: all traffic is sent to BIG-IQ management IP address and port TCP/443 (configurabile from nicstart.bat)

<img src="/images/portable-windows.1.jpg"/>

- When the NGINX Instance Counter has started, it can be queried sending a GET request to http://127.0.0.1:5000/instances

<img src="/images/portable-windows.2.jpg"/>
