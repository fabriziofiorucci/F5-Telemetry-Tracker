@echo off

rem ### Optional HTTP(S) proxy
rem set HTTP_PROXY=http(s)://username:password@proxy_ip:port
rem set HTTPS_PROXY=http(s)://username:password@proxy_ip:port

rem ### Section to use when polling NGINX Controller

rem set NGINX_CONTROLLER_TYPE=NGINX_CONTROLLER
rem set NGINX_CONTROLLER_FQDN=https://nginx-controller.ff.lan:443
rem set NGINX_CONTROLLER_USERNAME=username@domain
rem set NGINX_CONTROLLER_PASSWORD=thepassword

rem ### Section to use when polling NGINX Instance Manager

rem set NGINX_CONTROLLER_TYPE=NGINX_INSTANCE_MANAGER
rem set NGINX_CONTROLLER_FQDN=http://127.0.0.1:11000
rem set NGINX_CONTROLLER_USERNAME=username@domain
rem set NGINX_CONTROLLER_PASSWORD=thepassword

rem ### Section to use when polling BIG-IQ

rem set NGINX_CONTROLLER_TYPE=BIG_IQ
rem set NGINX_CONTROLLER_FQDN=https://bigiq.ff.lan
rem set NGINX_CONTROLLER_USERNAME=username
rem set NGINX_CONTROLLER_PASSWORD=thepassword

rem ### Section to use when using push in pushgateway mode (basic auth username/password are optional)

rem set STATS_PUSH_ENABLE=true
rem set STATS_PUSH_MODE=NGINX_PUSH
rem set STATS_PUSH_URL=http://pushgateway.nginx.ff.lan
rem ### STATS_PUSH_INTERVAL in seconds
rem set STATS_PUSH_INTERVAL=10
rem set STATS_PUSH_USERNAME=authusername
rem set STATS_PUSH_PASSWORD=authpassword

rem ### Section to use when using push in custom mode (basic auth username/password are optional) - STATS_PUSH_ENABLE is mandatory

set STATS_PUSH_ENABLE=false
set STATS_PUSH_MODE=CUSTOM
set STATS_PUSH_URL=http://192.168.1.18/callHome
rem ### STATS_PUSH_INTERVAL in seconds
set STATS_PUSH_INTERVAL=10
set STATS_PUSH_USERNAME=authusername
set STATS_PUSH_PASSWORD=authpassword

rem ### Section to use when using e-mail based push - EMAIL_ENABLED is mandatory
set EMAIL_ENABLED=false
set EMAIL_SERVER=smtp.mydomain.tld
rem ### Port 25 for SMTP, 465 for SMTP over TLS
set EMAIL_SERVER_PORT=25
rem ### EMAIL_SERVER_TYPE can be: starttls, ssl, plaintext
set EMAIL_SERVER_TYPE=starttls
set EMAIL_SENDER=sender@domain.tld
set EMAIL_RECIPIENT=recipient@domain.tld
rem ### EMAIL_INTERVAL in minutes
set EMAIL_INTERVAL=15
rem ### Optional for SMTP authentication
set EMAIL_AUTH_USER=username@domain
set EMAIL_AUTH_PASS=thepassword

NGINX-InstanceCounter.exe
