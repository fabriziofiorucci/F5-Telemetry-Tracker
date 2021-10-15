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
python -m nuitka --follow-imports --onefile app.py
```

- Edit and use the provided nicstart.sh script to run the generated image
