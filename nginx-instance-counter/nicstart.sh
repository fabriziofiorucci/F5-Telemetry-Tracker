#!/bin/bash

### Section to use when polling NGINX Controller

#export NGINX_CONTROLLER_TYPE=NGINX_CONTROLLER
#export NGINX_CONTROLLER_FQDN="https://nginx-controller.ff.lan:443"
#export NGINX_CONTROLLER_USERNAME="username@domain"
#export NGINX_CONTROLLER_PASSWORD="thepassword"

### Section to use when polling NGINX Instance Manager

#export NGINX_CONTROLLER_TYPE=NGINX_INSTANCE_MANAGER
#export NGINX_CONTROLLER_FQDN="https://nim.ff.lan:11000"
#export NGINX_CONTROLLER_USERNAME="username@domain"
#export NGINX_CONTROLLER_PASSWORD="thepassword"

### Section to use when using push in pushgateway mode (basic auth username/password are optional)

#export STATS_PUSH_ENABLE="true"
#export STATS_PUSH_MODE=NGINX_PUSH
#export STATS_PUSH_URL="http://pushgateway.nginx.ff.lan"
#export STATS_PUSH_INTERVAL=10
#export STATS_PUSH_USERNAME="authusername"
#export STATS_PUSH_PASSWORD="authpassword"

### Section to use when using push in custom mode (basic auth username/password are optional)

#export STATS_PUSH_ENABLE="true"
#export STATS_PUSH_MODE=CUSTOM
#export STATS_PUSH_URL="http://192.168.1.18/callHome"
#export STATS_PUSH_INTERVAL=10
#export STATS_PUSH_USERNAME="authusername"
#export STATS_PUSH_PASSWORD="authpassword"

python3 app.py
