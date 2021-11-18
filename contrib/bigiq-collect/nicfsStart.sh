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

python3 nicfs.py $WORKDIR &
NICFS_PID=$!

export NGINX_CONTROLLER_TYPE=BIG_IQ
export NGINX_CONTROLLER_FQDN="http://127.0.0.1:5001"
export NGINX_CONTROLLER_USERNAME="notused"
export NGINX_CONTROLLER_PASSWORD="notused"

python3 ../../nginx-instance-counter/app.py
kill $NICFS_PID

rm -rf $WORKDIR
