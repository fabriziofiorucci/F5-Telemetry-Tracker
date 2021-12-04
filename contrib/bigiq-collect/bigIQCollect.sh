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

echo "-> Data collection completed, building tarfile"
TARFILE=$OUTPUTROOT/`date +"%Y%m%d-%H%M"`-bigIQCollect.tgz
tar zcmf $TARFILE $OUTPUTDIR 2>/dev/null
rm -rf $OUTPUTDIR

echo "-> All done, copy $TARFILE to your local host using scp"
