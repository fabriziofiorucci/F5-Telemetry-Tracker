FROM ubuntu:latest
RUN apt-get update

RUN apt-get install -y -q build-essential python3-pip python3-dev python3-simplejson git nano curl
RUN pip3 install --upgrade flask
RUN pip3 install --upgrade virtualenv

RUN mkdir deployment
RUN virtualenv /deployment/env/
RUN /deployment/env/bin/python -m pip install --upgrade pip
RUN /deployment/env/bin/pip3 install flask
RUN /deployment/env/bin/pip3 install requests
WORKDIR /deployment
COPY app.py .

CMD env/bin/python3 app.py
