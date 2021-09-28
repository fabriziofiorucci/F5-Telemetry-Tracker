#!/bin/bash

### Section to use when polling NGINX Controller

#export NGINX_CONTROLLER_TYPE=NGINX_CONTROLLER
#export NGINX_CONTROLLER_FQDN="https://nginx-controller.ff.lan:443"
#export NGINX_CONTROLLER_USERNAME="username@domain"
#export NGINX_CONTROLLER_PASSWORD="thepassword"

### Section to use when polling NGINX Instance Manager

export NGINX_CONTROLLER_TYPE=NGINX_INSTANCE_MANAGER
export NGINX_CONTROLLER_FQDN="http://127.0.0.1:11000"
export NGINX_CONTROLLER_USERNAME="username@domain"
export NGINX_CONTROLLER_PASSWORD="thepassword"

### Section to use when polling BIG-IQ

#export NGINX_CONTROLLER_TYPE=BIG_IQ
#export NGINX_CONTROLLER_FQDN="https://bigiq.ff.lan"
#export NGINX_CONTROLLER_USERNAME="admin"
#export NGINX_CONTROLLER_PASSWORD="admin"

### Section to use when using push in pushgateway mode (basic auth username/password are optional)

#export STATS_PUSH_ENABLE="true"
#export STATS_PUSH_MODE=NGINX_PUSH
#export STATS_PUSH_URL="http://pushgateway.nginx.ff.lan"
# STATS_PUSH_INTERVAL in seconds
#export STATS_PUSH_INTERVAL=10
#export STATS_PUSH_USERNAME="authusername"
#export STATS_PUSH_PASSWORD="authpassword"

### Section to use when using push in custom mode (basic auth username/password are optional) - STATS_PUSH_ENABLE is mandatory

export STATS_PUSH_ENABLE="false"
export STATS_PUSH_MODE=CUSTOM
export STATS_PUSH_URL="http://192.168.1.18/callHome"
# STATS_PUSH_INTERVAL in seconds
export STATS_PUSH_INTERVAL=10
export STATS_PUSH_USERNAME="authusername"
export STATS_PUSH_PASSWORD="authpassword"

### Section to use when using e-mail based push - EMAIL_ENABLED is mandatory
export EMAIL_ENABLED="true"
export EMAIL_SERVER="smtp.mydomain.tld"
# Port 25 for SMTP, 465 for SMTP over TLS
export EMAIL_SERVER_PORT=25
# EMAIL_SERVER_TYPE can be: starttls, ssl, plaintext
export EMAIL_SERVER_TYPE="starttls"
export EMAIL_SENDER="sender@domain.tld"
export EMAIL_RECIPIENT="recipient@domain.tld"
# EMAIL_INTERVAL in minutes
export EMAIL_INTERVAL=15
# Optional for SMTP authentication
export EMAIL_AUTH_USER="username@domain"
export EMAIL_AUTH_PASS="thepassword"

python3 app.py
