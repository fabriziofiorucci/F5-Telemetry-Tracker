#!/bin/bash

#
# Usage
#
usage() {
BANNER="F5 Telemetry Tracker - https://github.com/fabriziofiorucci/F5-Telemetry-Tracker\n\n
This script is used to deploy/remove F5TT with docker-compose\n\n
=== Usage:\n\n
$0 [options]\n\n
=== Options:\n\n
-h\t\t\t- This help\n\n
-c [start|stop]\t- Deployment command\n
-t [bigiq|nim]\t\t- Deployment type\n\n
-s [url]\t\t- BIG-IQ/NGINX Instance Manager URL\n
-u [username]\t\t- BIG-IQ/NGINX Instance Manager username\n
-p [password]\t\t- BIG-IQ/NGINX Instance Manager password\n\n
=== Examples:\n\n
Deploy F5TT for BIG-IQ:\t\t\t$0 -c start -t bigiq -s https://<BIGIQ_ADDRESS> -u <username> -p <password>\n
Remove F5TT for BIG-IQ:\t\t\t$0 -c stop -t bigiq\n
Deploy F5TT for NGINX Instance Manager:\t$0 -c start -t nim -s https://<NGINX_INSTANCE_MANAGER_ADDRESS> -u <username> -p <password>\n
Remove F5TT for NGINX Instance Manager:\t$0 -c stop -t nim\n
"

echo -e $BANNER 2>&1
exit 1
}

#
# F5TT deployment
# parameters: [bigiq|nginx] [controlplane URL] [username] [password]
#
f5tt_start() {
if [ "$#" != 4 ]
then
	exit
fi

MODE=$1

# Docker compose variables
USERNAME=`whoami`
export USERID=`id -u $USERNAME`
export USERGROUP=`id -g $USERNAME`

export DATAPLANE_FQDN=$2
export DATAPLANE_USERNAME=$3
export DATAPLANE_PASSWORD=$4

echo "-> Deploying F5 Telemetry Tracker for $MODE at $DATAPLANE_FQDN" 
echo "Creating persistent storage directories under /opt/f5tt ..."
echo "Enter sudo password if prompted"

sudo bash -c "mkdir -p /opt/f5tt;chown $USERID:$USERGROUP /opt/f5tt"

if [ "$MODE" = "nim" ]
then
	mkdir -p /opt/f5tt/{prometheus,grafana/data,grafana/log,grafana/plugins,clickhouse/data,clickhouse/logs}
else
	mkdir -p /opt/f5tt/{prometheus,grafana/data,grafana/log,grafana/plugins}
fi

COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME-$MODE -f $DOCKER_COMPOSE_YAML-$MODE.yaml up -d --remove-orphans
}

#
# F5TT removal
# parameters: [bigiq|nginx]
#
f5tt_stop() {
if [ "$#" != 1 ]
then
	echo "Extra commandline parameters, aborting"
	exit
fi

MODE=$1

# Docker compose variables
USERNAME=`whoami`
export USERID=`id -u $USERNAME`
export USERGROUP=`id -g $USERNAME`
export DATAPLANE_FQDN=""
export DATAPLANE_USERNAME=""
export DATAPLANE_PASSWORD=""

echo "-> Undeploying F5 Telemetry Tracker for $MODE"

COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME-$MODE -f $DOCKER_COMPOSE_YAML-$MODE.yaml down
}

#
# Main
#

DOCKER_COMPOSE_YAML=f5tt-compose
PROJECT_NAME=f5tt

while getopts 'hc:t:s:u:p:' OPTION
do
        case "$OPTION" in
                h)
                        echo -e $BANNER
                        exit
                ;;
                c)
                        ACTION=$OPTARG
                ;;
                t)
                        MODE=$OPTARG
                ;;
		s)
			DATAPLANE_URL=$OPTARG
		;;
		u)
			DATAPLANE_USERNAME=$OPTARG
		;;
		p)
			DATAPLANE_PASSWORD=$OPTARG
		;;
        esac
done

if [ -z "${ACTION}" ] || [ -z "${MODE}" ] || [[ ! "${ACTION}" == +(start|stop) ]] || [[ ! "${MODE}" == +(bigiq|nim) ]] ||
	([ "${ACTION}" = "start" ] && ([ -z "${DATAPLANE_URL}" ] || [ -z "${DATAPLANE_USERNAME}" ] || [ -z "${DATAPLANE_PASSWORD}" ]))
then
	usage
fi

f5tt_$ACTION $MODE $DATAPLANE_URL $DATAPLANE_USERNAME $DATAPLANE_PASSWORD
