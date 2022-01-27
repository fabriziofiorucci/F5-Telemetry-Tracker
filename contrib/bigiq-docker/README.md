# F5 Telemetry Tracker on BIG-IQ CM Docker

## Description

The `f5tt-bigiq-docker.sh` script can be used to run F5TT as a container on a BIG-IQ CM 8.1 virtual machine.

BIG-IQ CM 8.1 must be able to pull docker images from docker hub.

If BIG-IQ CM is airgapped (no access to the Internet) [these steps](/contrib/bigiq-docker/AIRGAPPED.md) must be followed

## Installation

- Copy (scp) `f5tt-bigiq-docker.sh` from to BIG-IQ CM 8.1 instance, under /tmp/

```
$ scp f5tt-bigiq-docker.sh root@bigiq.f5:/tmp/
Password: 
f5tt-bigiq-docker.sh                         100% 2440     4.7MB/s   00:00    
$ 
```

- SSH to the BIG-IQ CM instance and run the script with no parameters to display the help banner

```
$ ssh root@bigiq.f5
Password: 
Last login: Wed Jan 26 16:44:26 2022 from 192.168.1.26
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh 
$ ./f5tt-bigiq-docker.sh 
F5 Telemetry Tracker - https://github.com/fabriziofiorucci/F5-Telemetry-Tracker

 This tool manages F5 Telemetry Tracker running on docker on a BIG-IQ Centralized Manager VM.

 === Usage:

 ./f5tt-bigiq-docker.sh [options]

 === Options:

 -h             - This help
 -s             - Start F5 Telemetry Tracker
 -k             - Stop (kill) F5 Telemetry Tracker
 -c             - Check F5 Telemetry Tracker run status
 -u [username]  - BIG-IQ username (batch mode)
 -p [password]  - BIG-IQ password (batch mode)
 -f             - Fetch JSON report
 -a             - All-in-one: start F5 Telemetry Tracker, collect JSON report and stop F5 Telemetry Tracker

 === Examples:

 Start:
        Interactive mode:       ./f5tt-bigiq-docker.sh -s
        Batch mode:             ./f5tt-bigiq-docker.sh -s -u [username] -p [password]
 Stop:
        ./f5tt-bigiq-docker.sh -k
 Fetch JSON:
        ./f5tt-bigiq-docker.sh -f
 All-in-one:
        ./f5tt-bigiq-docker.sh -a
```

## Usage - manual mode

- Start F5 Telemetry Tracker on BIG-IQ CM. Enter BIG-IQ admin username and the password

```
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh -s
Username: admin
Password: 
F5 Telemetry Tracker started on http://192.168.1.71:5000
[root@bigiq:Active:Standalone] config # 
```

- Query F5 Telemetry Tracker from another terminal session / system to get the target JSON file

Uncompressed output:

```
$ curl http://192.168.1.71:5000/instances
{"instances":[{"bigip":2,"hwTotals":[{"F5-VE":2}],"swTotals":[{"H-VE-AFM":1,"H-VE-AWF":1,"H-VE-LTM":2,"H-VE-APM":1,"H-VE-DNS":1}]}],"details":[{"inventoryTimestamp":1641986071513,"inventoryStatus":"full"[...]}
```

Compressed output:

```
$ curl -s -H "Accept-Encoding: gzip" http://192.168.1.71:5000/instances --output output-json.gz
```

- Stop F5 Telemetry Tracker:

```
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh -k
F5 Telemetry Tracker stopped
[root@bigiq:Active:Standalone] config # 
```

## Usage - all-in-one mode

- Start F5 Telemetry Tracker on BIG-IQ CM in all-in-one mode. Enter BIG-IQ admin username and the password

```
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh -a
Username: admin
Password: 
F5 Telemetry Tracker started on http://192.168.1.71:5000
Collecting report...
JSON report generated, copy /tmp/20220126-1851-instances.json to your local host using scp
F5 Telemetry Tracker stopped
[root@bigiq:Active:Standalone] config #
```

- Collect (scp) the generated JSON report
