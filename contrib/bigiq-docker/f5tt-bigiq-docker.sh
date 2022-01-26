#!/bin/bash

BANNER="F5 Telemetry Tracker - https://github.com/fabriziofiorucci/F5-Telemetry-Tracker\n\n
This tool manages F5 Telemetry Tracker running on docker on a BIG-IQ Centralized Manager VM.\n\n
=== Usage:\n\n
$0 [options]\n\n
=== Options:\n\n
-h\t\t- This help\n
-s\t\t- Start F5 Telemetry Tracker\n
-k\t\t- Stop (kill) F5 Telemetry Tracker\n
-c\t\t- Check F5 Telemetry Tracker run status\n
-u [username]\t- BIG-IQ username (batch mode)\n
-p [password]\t- BIG-IQ password (batch mode)\n
-f\t\t- Fetch JSON report\n
-a\t\t- All-in-one: start F5 Telemetry Tracker, collect JSON report and stop F5 Telemetry Tracker\n\n
=== Examples:\n\n
Start:\n
\tInteractive mode:\t$0 -s\n
\tBatch mode:\t\t$0 -s -u [username] -p [password]\n
Stop:\n
\t$0 -k\n
Fetch JSON:\n
\t$0 -f\n
All-in-one:\n
\t$0 -a\n
"

while getopts 'skhcfau:p:' OPTION
do
        case "$OPTION" in
                h)
                        echo -e $BANNER
                        exit
                ;;
                u)
                        BIGIQ_USERNAME=$OPTARG
                ;;
                p)
                        BIGIQ_PASSWORD=$OPTARG
                ;;
		s)
			MODE="start"
		;;
		k)
			MODE="stop"
		;;
		c)
			CHECK=`docker ps -q -f name=f5tt`
			if [ "$CHECK" = "" ]
			then
				echo "F5 Telemetry Tracker not running"
				exit 0
			else
				echo "F5 Telemetry Tracker running"
				exit 1
			fi
		;;
		f)
			$0 -c >/dev/null
			F5TT_STATUS=$?

			if [ $F5TT_STATUS = 0 ]
			then
				echo "F5 Telemetry Tracker not running"
			else
				echo "Collecting report..."
				JSONFILE=/tmp/`date +"%Y%m%d-%H%M"`-instances.json
				curl -s http://127.0.0.1:5000/instances > $JSONFILE

				echo "JSON report generated, copy $JSONFILE to your local host using scp"
			fi

			exit
		;;
		a)
			$0 -s
			sleep 5
			$0 -f
			$0 -k
			exit
		;;
        esac
done

if [ "$MODE" = "" ]
then
        echo -e $BANNER
        exit
fi

if [ "$MODE" = "start" ]
then
	if [ "$BIGIQ_USERNAME" = "" ] || [ "$BIGIQ_PASSWORD" = "" ]
	then
		read -p "Username: " BIGIQ_USERNAME
		read -sp "Password: " BIGIQ_PASSWORD
		echo
	fi
fi

DOCKER_IMAGE=fiorucci/f5-telemetry-tracker:1.1
DOCKER_IP=`ip add show docker0 | grep inet\  | awk '{print $2}' | awk -F\/ '{print $1}'`

case $MODE in
	'start')
		mv /etc/systemd/system/docker.service.d/http-proxy.conf /etc/systemd/system/docker.service.d/http-proxy.conf.disabled 2>/dev/null
		systemctl stop docker 2>/dev/null
		systemctl daemon-reload 2>/dev/null
		systemctl start docker 2>/dev/null

		docker run -d --name f5tt \
		-p 5000:5000 \
		-e NGINX_CONTROLLER_TYPE=BIG_IQ \
		-e NGINX_CONTROLLER_FQDN="https://$DOCKER_IP" \
		-e NGINX_CONTROLLER_USERNAME=$BIGIQ_USERNAME \
		-e NGINX_CONTROLLER_PASSWORD=$BIGIQ_PASSWORD \
		fiorucci/f5-telemetry-tracker:1.1 2>/dev/null >/dev/null

		MGMT_IP=`ip add show mgmt | grep inet\  | awk '{print $2}' | awk -F\/ '{print $1}'`
		echo "F5 Telemetry Tracker started on http://$MGMT_IP:5000"
	;;
	'stop')
		docker stop f5tt 2>/dev/null >/dev/null
		docker rm f5tt 2>/dev/null >/dev/null

		mv /etc/systemd/system/docker.service.d/http-proxy.conf.disabled /etc/systemd/system/docker.service.d/http-proxy.conf 2>/dev/null
		systemctl stop docker 2>/dev/null
		systemctl daemon-reload 2>/dev/null
		systemctl start docker 2>/dev/null

		echo "F5 Telemetry Tracker stopped"
	;;
esac

