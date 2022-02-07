#!/bin/bash

if [ "$1" = "" ]
then
        echo "$0 [tgz file]"
        exit
fi

TGZFILE=$1
WORKDIR=`mktemp -d`

echo $WORKDIR

tar zxmf $TGZFILE -C $WORKDIR
mv $WORKDIR/*/*/*json $WORKDIR

python3 f5ttfs.py $WORKDIR &
F5TTFS_PID=$!

export DATAPLANE_TYPE=BIG_IQ
export DATAPLANE_FQDN="http://127.0.0.1:5001"
export DATAPLANE_USERNAME="notused"
export DATAPLANE_PASSWORD="notused"

### Optional NIST API Key for CVE tracking (https://nvd.nist.gov/developers/request-an-api-key)
#export NIST_API_KEY=xxxxxxx

python3 ../../f5tt/app.py
kill $F5TTFS_PID

rm -rf $WORKDIR
