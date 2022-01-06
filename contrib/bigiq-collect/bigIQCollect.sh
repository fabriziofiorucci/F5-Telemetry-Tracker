#!/bin/bash

#
# Run with:
#
# bash /tmp/bigIQCollect.sh username password
#

if [ "$2" = "" ]
then
	echo "$0 [username] [password]"
	exit
fi

BIGIQ_USERNAME=$1
BIGIQ_PASSWORD=$2

OUTPUTROOT=/tmp
OUTPUTDIR=`mktemp -d`

echo "-> Reading device list"
restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices > $OUTPUTDIR/1.bigIQCollect.json

echo "-> Reading system provisioning"
restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/shared/current-config/sys/provision > $OUTPUTDIR/2.bigIQCollect.json

echo "-> Reading device inventory"
restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/device/tasks/device-inventory > $OUTPUTDIR/3.bigIQCollect.json

echo "-> Reading device inventory details"
INV_ID=`restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/device/tasks/device-inventory| jq -r 'select(.items[].status=="FINISHED")|.items[0].resultsReference.link' | head -n1 | awk -F \/ '{print $9}'`
restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/device/reports/device-inventory/$INV_ID/results > $OUTPUTDIR/4.bigIQCollect.json

MACHINE_IDS=`cat $OUTPUTDIR/4.bigIQCollect.json | jq -r '.items[].infoState.machineId'`

for M in $MACHINE_IDS
do
	echo "-> Reading device info for [$M]"
	restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/system/machineid-resolver/$M > $OUTPUTDIR/machineid-resolver-$M.json
done

echo "-> Reading device telemetry"
ALL_TELEMETRY="
bigip-cpu|cpu-usage|-1H|5|MINUTES
bigip-cpu|cpu-usage|-1W|3|HOURS
bigip-cpu|cpu-usage|-1M|12|HOURS
bigip-memory|free-ram|-1H|5|MINUTES
bigip-memory|free-ram|-1W|3|HOURS
bigip-memory|free-ram|-1M|12|HOURS
"

AUTH_TOKEN=`curl -ks -X POST 'https://127.0.0.1/mgmt/shared/authn/login' -H 'Content-Type: text/plain' -d '{"username": "'$BIGIQ_USERNAME'","password": "'$BIGIQ_PASSWORD'"}' | jq '.token.token' -r`

for T in $ALL_TELEMETRY
do
	T_MODULE=`echo $T | awk -F\| '{print $1}'`
	T_METRICSET=`echo $T | awk -F\| '{print $2}'`
	T_TIMERANGE=`echo $T | awk -F\| '{print $3}'`
	T_GRAN_DURATION=`echo $T | awk -F\| '{print $4}'`
	T_GRAN_UNIT=`echo $T | awk -F\| '{print $5}'`

	echo "- $T_MODULE / $T_METRICSET / $T_TIMERANGE / $T_GRAN_DURATION / $T_GRAN_UNIT"

	TELEMETRY_JSON='{
    "kind": "ap:query:stats:byEntities",
    "module": "'$T_MODULE'",
    "timeRange": {
            "from": "'$T_TIMERANGE'",
            "to": "now"
    },
    "dimension": "hostname",
    "aggregations": {
            "'$T_METRICSET'$avg-value-per-event": {
                    "metricSet": "'$T_METRICSET'",
                    "metric": "avg-value-per-event"
            }
    },
    "timeGranularity": {
      "duration": '$T_GRAN_DURATION',
      "unit": "'$T_GRAN_UNIT'"
    },
    "limit": 1000
}'

	TELEMETRY_OUTPUT=`curl -ks -X POST https://127.0.0.1/mgmt/ap/query/v1/tenants/default/products/device/metric-query -H 'X-F5-Auth-Token: '$AUTH_TOKEN -H 'Content-Type: application/json' -d "$TELEMETRY_JSON"`

	echo $TELEMETRY_OUTPUT > $OUTPUTDIR/telemetry-$T_MODULE-$T_TIMERANGE.json
done

echo "-> Data collection completed, building tarfile"
TARFILE=$OUTPUTROOT/`date +"%Y%m%d-%H%M"`-bigIQCollect.tgz
tar zcmf $TARFILE $OUTPUTDIR 2>/dev/null
rm -rf $OUTPUTDIR

echo "-> All done, copy $TARFILE to your local host using scp"
