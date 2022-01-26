# F5 Telemetry Tracker Docker image setup on airgapped BIG-IQ CM

## Description

This howto can be used to load F5 Telemetry Tracker docker image on an airgapped BIG-IQ CM virtual machine.
After going through these instructions, F5 Telemetry Tracker can be used following [these steps](/contrib/bigiq-docker).

All steps shall be performed on a Linux host with docker installed and running

- Pull the F5 Telemetry Tracker docker image from docker hub

```
$ docker pull fiorucci/f5-telemetry-tracker:1.1 
1.1: Pulling from fiorucci/f5-telemetry-tracker
Digest: sha256:75840af5bb9a44810db16c6b3d1465fbb244428255078cc7e83d50074783691b
Status: Image is up to date for fiorucci/f5-telemetry-tracker:1.1
docker.io/fiorucci/f5-telemetry-tracker:1.1
$
```

- Save the image to a local tar file

```
$ docker save fiorucci/f5-telemetry-tracker:1.1 -o f5tt-docker.tar
$
```

- Copy the image to the BIG-IQ CM virtual machine

```
$ scp f5tt-docker.tar root@bigiq.f5:/shared/images/tmp/
Password: 
f5tt-docker.tar                                100%  697MB  84.0MB/s   00:08
$
```

- Connect to the BIG-IQ CM virtual machine

```
$ ssh root@bigiq.f5
Password: 
Last login: Wed Jan 26 19:07:47 2022 from 192.168.1.26
[root@bigiq:Active:Standalone] config # 
```

- Load the docker image

```
[root@bigiq:Active:Standalone] config # docker load < /shared/images/tmp/f5tt-docker.tar 
0eba131dffd0: Loading layer [==================================================>]  75.16MB/75.16MB
a5244046e7ac: Loading layer [==================================================>]  32.76MB/32.76MB
a077edfdbded: Loading layer [==================================================>]    361MB/361MB
f71ee1993884: Loading layer [==================================================>]   16.2MB/16.2MB
48a8991c237c: Loading layer [==================================================>]  2.048kB/2.048kB
5b2c989fa2e0: Loading layer [==================================================>]  21.19MB/21.19MB
e403953bd06f: Loading layer [==================================================>]  2.938MB/2.938MB
854b239c3e92: Loading layer [==================================================>]  221.9MB/221.9MB
406b158efc4c: Loading layer [==================================================>]  16.38kB/16.38kB
c7532987c4b6: Loading layer [==================================================>]  9.216kB/9.216kB
a156e398b887: Loading layer [==================================================>]   7.68kB/7.68kB
ceb787a7c705: Loading layer [==================================================>]   7.68kB/7.68kB
ef6b7a028bea: Loading layer [==================================================>]   29.7kB/29.7kB
e7cdea9208ff: Loading layer [==================================================>]  7.168kB/7.168kB
Loaded image: fiorucci/f5-telemetry-tracker:1.1
[root@bigiq:Active:Standalone] config #
```

- Remove the docker image tar file

```
[root@bigiq:Active:Standalone] config # rm -f /shared/images/tmp/f5tt-docker.tar
[root@bigiq:Active:Standalone] config #
```
