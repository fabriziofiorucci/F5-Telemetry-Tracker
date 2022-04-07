#!/bin/bash

#
# Run with:
#
# bash /tmp/bigIQCollect.sh username password
#

BANNER="F5 Telemetry Tracker - https://github.com/fabriziofiorucci/F5-Telemetry-Tracker\n\n
This tool collects usage tracking data from BIG-IQ for offline postprocessing.\n\n
=== Usage:\n\n
$0 [options]\n\n
=== Options:\n\n
-h\t\t- This help\n
-i\t\t- Interactive mode\n
-u [username]\t- BIG-IQ username (batch mode)\n
-p [password]\t- BIG-IQ password (batch mode)\n\n
=== Examples:\n\n
Interactive mode:\t$0 -i\n
Batch mode:\t\t$0 -u [username] -p [password]\n
"

while getopts 'hiu:p:' OPTION
do
	case "$OPTION" in
		h)
			echo -e $BANNER
			exit
		;;
		i)
			read -p "Username: " BIGIQ_USERNAME
			read -sp "Password: " BIGIQ_PASSWORD
			echo
		;;
		u)
			BIGIQ_USERNAME=$OPTARG
		;;
		p)
			BIGIQ_PASSWORD=$OPTARG
		;;
	esac
done

if [ "$1" = "" ] || [ "$BIGIQ_USERNAME" = "" ] || [ "$BIGIQ_PASSWORD" = "" ]
then
	echo -e $BANNER
	exit
fi

AUTH_CHECK=`curl -ks -X POST 'https://127.0.0.1/mgmt/shared/authn/login' -H 'Content-Type: text/plain' -d '{"username": "'$BIGIQ_USERNAME'","password": "'$BIGIQ_PASSWORD'"}' | jq '.username' -r`

if [ "$AUTH_CHECK" == "null" ]
then
	echo "Wrong credentials: authentication failed"
	exit
fi

OUTPUTROOT=/tmp
OUTPUTDIR=`mktemp -d`

echo "-> Reading device list"
restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices > $OUTPUTDIR/1.bigIQCollect.json

echo "-> Reading system provisioning"
restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/shared/current-config/sys/provision > $OUTPUTDIR/2.bigIQCollect.json

echo "-> Reading device inventory"
restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/device/tasks/device-inventory > $OUTPUTDIR/3.bigIQCollect.json

echo "-> Reading device inventory details"
INVENTORIES=`restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/device/tasks/device-inventory`
INVENTORIES_LEN=`echo $INVENTORIES | jq '.items|length'`

echo "-> Found $INVENTORIES_LEN inventories"

if [ $INVENTORIES_LEN = 0 ]
then
	echo "Error: no inventory found - Please refer to https://support.f5.com/csp/article/K29144504 for more details"
	exit
fi

echo "-> Inventories summary"
echo $INVENTORIES | jq -r '.items[].status' | sort | uniq -c

INV_ID=`echo $INVENTORIES | jq -r '.items['$(expr $INVENTORIES_LEN - 1)'].resultsReference.link' | head -n1 | awk -F \/ '{print $9}'`

if [ ! "$INV_ID" = "" ]
then

restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/device/reports/device-inventory/$INV_ID/results > $OUTPUTDIR/4.bigIQCollect.json

MACHINE_IDS=`cat $OUTPUTDIR/4.bigIQCollect.json | jq -r '.items[].infoState.machineId'`

for M in $MACHINE_IDS
do
	echo "-> Reading device info for [$M]"
	restcurl -u $BIGIQ_USERNAME:$BIGIQ_PASSWORD /mgmt/cm/system/machineid-resolver/$M > $OUTPUTDIR/machineid-resolver-$M.json
done

echo "-> Reading device telemetry"
ALL_TELEMETRY="
bigip-cpu|cpu-usage|avg-value-per-event|-1H|5|MINUTES
bigip-cpu|cpu-usage|avg-value-per-event|-1W|3|HOURS
bigip-cpu|cpu-usage|avg-value-per-event|-30D|12|HOURS
bigip-memory|free-ram|avg-value-per-event|-1H|5|MINUTES
bigip-memory|free-ram|avg-value-per-event|-1W|3|HOURS
bigip-memory|free-ram|avg-value-per-event|-30D|12|HOURS
bigip-traffic-summary|server-connections|avg-value-per-sec|-1H|5|MINUTES
bigip-traffic-summary|server-connections|avg-value-per-sec|-1W|3|HOURS
bigip-traffic-summary|server-connections|avg-value-per-sec|-30D|12|HOURS
bigip-traffic-summary|client-bytes-in|avg-value-per-sec|-1H|5|MINUTES
bigip-traffic-summary|client-bytes-in|avg-value-per-sec|-1W|3|HOURS
bigip-traffic-summary|client-bytes-in|avg-value-per-sec|-30D|12|HOURS
bigip-traffic-summary|client-bytes-out|avg-value-per-sec|-1H|5|MINUTES
bigip-traffic-summary|client-bytes-out|avg-value-per-sec|-1W|3|HOURS
bigip-traffic-summary|client-bytes-out|avg-value-per-sec|-30D|12|HOURS
bigip-traffic-summary|server-bytes-in|avg-value-per-sec|-1H|5|MINUTES
bigip-traffic-summary|server-bytes-in|avg-value-per-sec|-1W|3|HOURS
bigip-traffic-summary|server-bytes-in|avg-value-per-sec|-30D|12|HOURS
bigip-traffic-summary|server-bytes-out|avg-value-per-sec|-1H|5|MINUTES
bigip-traffic-summary|server-bytes-out|avg-value-per-sec|-1W|3|HOURS
bigip-traffic-summary|server-bytes-out|avg-value-per-sec|-30D|12|HOURS
"

ALL_HOSTNAMES=""

AUTH_TOKEN=`curl -ks -X POST 'https://127.0.0.1/mgmt/shared/authn/login' -H 'Content-Type: text/plain' -d '{"username": "'$BIGIQ_USERNAME'","password": "'$BIGIQ_PASSWORD'"}' | jq '.token.token' -r`

for T in $ALL_TELEMETRY
do
	T_MODULE=`echo $T | awk -F\| '{print $1}'`
	T_METRICSET=`echo $T | awk -F\| '{print $2}'`
	T_METRIC=`echo $T | awk -F\| '{print $3}'`
	T_TIMERANGE=`echo $T | awk -F\| '{print $4}'`
	T_GRAN_DURATION=`echo $T | awk -F\| '{print $5}'`
	T_GRAN_UNIT=`echo $T | awk -F\| '{print $6}'`

	#echo "- $T_MODULE / $T_METRICSET / $T_METRIC / $T_TIMERANGE / $T_GRAN_DURATION / $T_GRAN_UNIT"

	TELEMETRY_JSON='{
    "kind": "ap:query:stats:byEntities",
    "module": "'$T_MODULE'",
    "timeRange": {
            "from": "'$T_TIMERANGE'",
            "to": "now"
    },
    "dimension": "hostname",
    "aggregations": {
            "'$T_METRICSET'$'$T_METRIC'": {
                    "metricSet": "'$T_METRICSET'",
                    "metric": "'$T_METRIC'"
            }
    },
    "timeGranularity": {
      "duration": '$T_GRAN_DURATION',
      "unit": "'$T_GRAN_UNIT'"
    },
    "limit": 1000
}'

	TELEMETRY_OUTPUT=`curl -ks -X POST https://127.0.0.1/mgmt/ap/query/v1/tenants/default/products/device/metric-query -H 'X-F5-Auth-Token: '$AUTH_TOKEN -H 'Content-Type: application/json' -d "$TELEMETRY_JSON"`
        OUTFILE=$OUTPUTDIR/telemetry-$T_MODULE-$T_METRICSET-$T_TIMERANGE.json

	echo $TELEMETRY_OUTPUT > $OUTFILE

	if [ "$ALL_HOSTNAMES" = "" ]
	then
		ALL_HOSTNAMES=`echo $TELEMETRY_OUTPUT |jq -r '.result.result[].hostname' 2>/dev/null`
	fi
done

## Datapoints telemetry

AUTH_TOKEN=`curl -ks -X POST 'https://127.0.0.1/mgmt/shared/authn/login' -H 'Content-Type: text/plain' -d '{"username": "'$BIGIQ_USERNAME'","password": "'$BIGIQ_PASSWORD'"}' | jq '.token.token' -r`

for TDP_HOSTNAME in $ALL_HOSTNAMES
do

echo "-> Reading device telemetry datapoints for $TDP_HOSTNAME"

for TDP in $ALL_TELEMETRY
do
	TDP_MODULE=`echo $TDP | awk -F\| '{print $1}'`
	TDP_METRICSET=`echo $TDP | awk -F\| '{print $2}'`
	TDP_METRIC=`echo $TDP | awk -F\| '{print $3}'`
	TDP_TIMERANGE=`echo $TDP | awk -F\| '{print $4}'`
	TDP_GRAN_DURATION=`echo $TDP | awk -F\| '{print $5}'`
	TDP_GRAN_UNIT=`echo $TDP | awk -F\| '{print $6}'`

	#echo "- $TDP_HOSTNAME -> $TDP_MODULE / $TDP_METRICSET / $TDP_METRIC / $TDP_TIMERANGE / $TDP_GRAN_DURATION / $TDP_GRAN_UNIT"

	TELEMETRY_DP_JSON='{
    "kind": "ap:query:stats:byTime",
    "module": "'$TDP_MODULE'",
    "timeRange": {
            "from": "'$TDP_TIMERANGE'",
            "to": "now"
    },
    "dimension": "hostname",
    "dimensionFilter": {
            "type": "eq",
            "dimension": "hostname",
            "value": "'$TDP_HOSTNAME'"
    },
    "aggregations": {
            "'$TDP_METRICSET'$'$TDP_METRIC'": {
                    "metricSet": "'$TDP_METRICSET'",
                    "metric": "'$TDP_METRIC'"
            }
    },
    "timeGranularity": {
      "duration": '$TDP_GRAN_DURATION',
      "unit": "'$TDP_GRAN_UNIT'"
    },
    "limit": 1000
}'

	TELEMETRY_DP_OUTPUT=`curl -ks -X POST https://127.0.0.1/mgmt/ap/query/v1/tenants/default/products/device/metric-query -H 'X-F5-Auth-Token: '$AUTH_TOKEN -H 'Content-Type: application/json' -d "$TELEMETRY_DP_JSON"`
        OUTFILE=$OUTPUTDIR/telemetry-datapoints-$TDP_HOSTNAME-$TDP_MODULE-$TDP_METRICSET-$TDP_TIMERANGE.json

	echo $TELEMETRY_DP_OUTPUT > $OUTFILE
done

done

### /Datapoints telemetry

fi

### Utility billing collection

AUTH_TOKEN=`curl -ks -X POST 'https://127.0.0.1/mgmt/shared/authn/login' -H 'Content-Type: text/plain' -d '{"username": "'$BIGIQ_USERNAME'","password": "'$BIGIQ_PASSWORD'"}' | jq '.token.token' -r`

UTB_ALLLICENSES=`curl -ks -X GET "https://127.0.0.1/mgmt/cm/device/licensing/pool/utility/licenses?$select=regKey,status" -H 'X-F5-Auth-Token: '$AUTH_TOKEN`
echo $UTB_ALLLICENSES > $OUTPUTDIR/utilitybilling-licenses.json

UTB_ALLREGKEYS=`echo $UTB_ALLLICENSES | jq -r '.items[]|.regKey'`

for REGKEY in $UTB_ALLREGKEYS
do
	echo "-> Collecting utility billing for regkey $REGKEY"
	REPORT_STATUS_JSON=`curl -ks -X POST https://127.0.0.1/mgmt/cm/device/tasks/licensing/utility-billing-reports -H 'X-F5-Auth-Token: '$AUTH_TOKEN -H 'Content-Type: application/json' -d '{"regKey": "'$REGKEY'","submissionMethod": "Automatic"}'`
	REPORT_STATUS_ID=`echo $REPORT_STATUS_JSON | jq -r '.selfLink' | awk -F\/ '{print $10}'`
	echo $REPORT_STATUS_JSON > $OUTPUTDIR/utilitybilling-createreport-$REGKEY

	sleep 4

	REPORT_DOWNLOAD_JSON=`curl -ks -X GET https://127.0.0.1/mgmt/cm/device/tasks/licensing/utility-billing-reports/$REPORT_STATUS_ID -H 'X-F5-Auth-Token: '$AUTH_TOKEN`
	REPORT_DOWNLOAD_FILE=`echo $REPORT_DOWNLOAD_JSON | jq -r '.reportUri' | awk -F\/ '{print $9}'`
	echo $REPORT_DOWNLOAD_JSON > $OUTPUTDIR/utilitybilling-reportstatus-$REPORT_STATUS_ID

	REPORT_JSON=`curl -ks -X GET https://127.0.0.1/mgmt/cm/device/licensing/license-reports-download/$REPORT_DOWNLOAD_FILE -H 'X-F5-Auth-Token: '$AUTH_TOKEN`
	echo $REPORT_JSON > $OUTPUTDIR/utilitybilling-billingreport-$REPORT_DOWNLOAD_FILE
done

### /Utility billing collection


echo "-> Data collection completed, building tarfile"
TARFILE=$OUTPUTROOT/`date +"%Y%m%d-%H%M"`-bigIQCollect.tgz
tar zcmf $TARFILE $OUTPUTDIR 2>/dev/null
rm -rf $OUTPUTDIR

echo "-> All done, copy $TARFILE to your local host using scp"
