@echo off

rem ### Optional listen address and port
rem set F5TT_ADDRESS=0.0.0.0
rem set F5TT_PORT=5000

rem ### Optional HTTP(S) proxy
rem set HTTP_PROXY=http(s)://username:password@proxy_ip:port
rem set HTTPS_PROXY=http(s)://username:password@proxy_ip:port

rem ### Optional NIST API Key for CVE tracking (https://nvd.nist.gov/developers/request-an-api-key)
rem set NIST_API_KEY=xxxxxxxx

rem ### Section to use when polling NGINX Controller

rem set NGINX_CONTROLLER_TYPE=NGINX_CONTROLLER
rem set NGINX_CONTROLLER_FQDN=https://nginx-controller.ff.lan:443
rem set NGINX_CONTROLLER_USERNAME=username@domain
rem set NGINX_CONTROLLER_PASSWORD=thepassword

rem ### Section to use when polling NGINX Instance Manager 1.x

rem set NGINX_CONTROLLER_TYPE=NGINX_INSTANCE_MANAGER
rem set NGINX_CONTROLLER_FQDN=http://127.0.0.1:11000
rem set NGINX_CONTROLLER_USERNAME=username@domain
rem set NGINX_CONTROLLER_PASSWORD=thepassword

rem ### Section to use when polling NGINX Instance Manager 2.x

rem set NGINX_CONTROLLER_TYPE=NGINX_MANAGEMENT_SYSTEM
rem set NGINX_CONTROLLER_FQDN=https://ubuntu.ff.lan
rem set NGINX_CONTROLLER_USERNAME=theusername
rem set NGINX_CONTROLLER_PASSWORD=thepassword

rem ### Section to use when polling BIG-IQ

rem set NGINX_CONTROLLER_TYPE=BIG_IQ
rem set NGINX_CONTROLLER_FQDN=https://bigiq.ff.lan
rem set NGINX_CONTROLLER_USERNAME=username
rem set NGINX_CONTROLLER_PASSWORD=thepassword

rem ### Section to use when using push in pushgateway mode (basic auth username/password are optional)

rem set STATS_PUSH_ENABLE=true
rem set STATS_PUSH_MODE=NGINX_PUSH
rem set STATS_PUSH_URL=http://pushgateway.f5tt.ff.lan
rem ### STATS_PUSH_INTERVAL in seconds
rem set STATS_PUSH_INTERVAL=10
rem set STATS_PUSH_USERNAME=authusername
rem set STATS_PUSH_PASSWORD=authpassword

rem ### Section to use when using push in custom mode (basic auth username/password are optional)

rem set STATS_PUSH_ENABLE=false
rem set STATS_PUSH_MODE=CUSTOM
rem set STATS_PUSH_URL=http://192.168.1.18/callHome
rem ### STATS_PUSH_INTERVAL in seconds
rem set STATS_PUSH_INTERVAL=10
rem set STATS_PUSH_USERNAME=authusername
rem set STATS_PUSH_PASSWORD=authpassword

rem ### Section to use when using e-mail based push
rem set EMAIL_ENABLED=false
rem set EMAIL_SERVER=smtp.mydomain.tld
rem ### Port 25 for SMTP, 465 for SMTP over TLS
rem set EMAIL_SERVER_PORT=25
rem ### EMAIL_SERVER_TYPE can be: starttls, ssl, plaintext
rem set EMAIL_SERVER_TYPE=starttls
rem set EMAIL_SENDER=sender@domain.tld
rem set EMAIL_RECIPIENT=recipient@domain.tld
rem ### EMAIL_INTERVAL in minutes
rem set EMAIL_INTERVAL=15
rem ### Optional for SMTP authentication
rem set EMAIL_AUTH_USER=username@domain
rem set EMAIL_AUTH_PASS=thepassword

F5-Telemetry-Tracker.exe
