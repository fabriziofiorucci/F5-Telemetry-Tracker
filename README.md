# NGINX Instance Counter

## Description

This tool helps tracking NGINX Plus instances managed by NGINX Controller and NGINX Instance Manager, and BIG-IP instances managed by BIG-IQ

It has been tested against:

- NGINX Controller 3.18, 3.18.2
- NGINX Instance Manager 1.0.1, 1.0.2, 1.0.3
- BIG-IQ 8.1.0

Communication to NGINX Controller / NGINX Instance Manager / BIG-IQ is based on REST API, current features are:

- REST API mode
  - /instances - returns JSON output
  - /metrics - returns Prometheus compliant output
- Push mode
  - POSTs instance statistics to a user-defined HTTP(S) URL (STATS_PUSH_MODE: CUSTOM)
  - Pushes instance statistics to pushgateway (STATS_PUSH_MODE: NGINX_PUSH)
  - Basic authentication support
  - User-defined push interval (in seconds)

## Deployment modes

Pull mode: Instance Counter fetches stats

<img src="./images/nginx-imagecounter-pull.jpg"/>

Push mode: Instance Counter pushes stats to a remote data collection and visualization environment (suitable for distributed setups)

<img src="./images/nginx-imagecounter-push.jpg"/>

## Prerequisites

- Kubernetes or Openshift cluster
- Private registry to push the NGINX Instance Counter image
- NGINX Controller 3.18, 3.18.2 or NGINX Instance Manager 1.0.1, 1.0.2, 1.0.3 or BIG-IP 8.1.0

# How to build

## For Kubernetes/Openshift

The NGINX Instance Counter image is available on Docker Hub as:

```
fiorucci/nginx-instance-counter:2.4
```

The 1.instancecounter.yaml file references that by default.

If you need to build and push NGINX your own image to a private registry:

```
git clone fabriziofiorucci/NGINX-InstanceCounter
cd NGINX-InstanceCounter/nginx-instance-counter

docker build --no-cache -t PRIVATE_REGISTRY:PORT/nginx-instance-counter:2.4 .
docker push PRIVATE_REGISTRY:PORT/nginx-instance-counter:2.4
```

## As a native python application

NGINX Instance Counter requires:

- Any Linux distribution
- Python 3 (tested on 3.9+)
- [Flask framework](https://flask.palletsprojects.com/en/2.0.x/)
- [Requests](https://docs.python-requests.org/en/master/)

nginx-instance-counter/nicstart.sh is a sample script to run NGINX Instance Counter from bash

# How to deploy

## For Kubernetes/Openshift

```
cd NGINX-InstanceCounter/manifests
```

Edit 1.instancecounter.yaml to customize:

- image name:
  - To be set to your private registry image (only if not using the image available on Docker Hub)
- environment variables:
  - NGINX_CONTROLLER_TYPE - can be NGINX_CONTROLLER, NGINX_INSTANCE_MANAGER or BIG_IQ
  - NGINX_CONTROLLER_FQDN - the FQDN of your NGINX Controller / NGINX Instance Manager / BIG-IQ instance - format must be http[s]://FQDN:port
  - NGINX_CONTROLLER_USERNAME - the username for authentication
  - NGINX_CONTROLLER_PASSWORD - the password for authentication

  - STATS_PUSH_ENABLE - if set to "true" push mode is enabled, disabled it set to "false"
  - STATS_PUSH_MODE - either CUSTOM or NGINX_PUSH, to push (HTTP POST) JSON to custom URL and to push metrics to pushgateway, respectively
  - STATS_PUSH_URL - the URL where to push statistics
  - STATS_PUSH_INTERVAL - the interval in seconds between two consecutive push
  - STATS_PUSH_USERNAME - (optional) the username for POST Basic Authentication
  - STATS_PUSH_PASSWORD - (optional) the password for POST Basic Authentication
- Ingress host:
  - By default it is set to counter.nginx.ff.lan

For standalone operations (ie. REST API + optional push to custom URL):

```
kubectl apply -f 0.ns.yaml
kubectl apply -f 1.instancecounter.yaml
```

To push statistics to pushgateway also apply:

```
kubectl apply -f 2.prometheus.yaml
kubectl apply -f 3.grafana.yaml
kubectl apply -f 4.pushgateway.yaml
```

By default 2.prometheus.yaml is configured for push mode, it must be edited decommenting the relevant section for pull mode

To setup visualization:

- Grafana shall be configured with a Prometheus datasource using by default http://prometheus.nginx.ff.lan
- Import the dashboard NGINX-InstanceCounter-dashboard.json in Grafana

Service names created by default as Ingress resources are:

- counter.nginx.ff.lan - REST API and Prometheus scraping endpoint
- pushgateway.nginx.ff.lan - Pushgateway web GUI
- prometheus.nginx.ff.lan - Prometheus web GUI
- grafana.nginx.ff.lan - Grafana visualization web GUI

## As a native python application

Edit nginx-instance-counter/nicstart.sh and run it

## Using F5 Support solution

See F5 Support solution at https://support.f5.com/csp/article/K83394355

# Usage

## REST API mode

To get instance statistics in JSON format:

NGINX Instance Manager

```
$ curl -s http://counter.nginx.ff.lan/instances | jq
{
  "subscription": {
    "id": "NGX-Subscription-1-TRL-XXXXXX",
    "type": "INSTANCE_MANAGER",
    "version": "1.0.2",
    "serial": "6232847160738694"
  },
  "instances": [
    {
      "nginx_plus_online": 0,
      "nginx_oss_online": 1
    }
  ],
  "details": [
    {
      "instance_id": "ee3f2f76-aa22-4182-b643-ba298cc0f758",
      "uname": "Linux ubuntu 5.4.0-80-generic #90-Ubuntu SMP Fri Jul 9 22:49:44 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux",
      "containerized": "False",
      "type": "oss",
      "version": "1.18.0",
      "last_seen": "2021-08-18T07:57:11.670746604Z"
    }
  ]
}
```

NGINX Controller

```
$ curl -s http://ubuntu:5000/instances | jq 
{
  "subscription": {
    "id": "T0XXXXXX",
    "type": "NGINX Controller",
    "version": "3.18.2"
  },
  "instances": [
    {
      "location": "devops",
      "nginx_plus_online": 0,
      "nginx_plus_offline": 0
    },
    {
      "location": "production",
      "nginx_plus_online": 0,
      "nginx_plus_offline": 0
    },
    {
      "location": "unspecified",
      "nginx_plus_online": 2,
      "nginx_plus_offline": 1
    }
  ],
  "details": [
    {
      "instance_id": "f6f6dff5-2a3b-477e-98ae-1fb1da0339cc",
      "uname": "linux Ubuntu 18.04.5 LTS (Bionic Beaver) x86_64 QEMU Virtual CPU version 2.5+",
      "containerized": "True",
      "type": "plus",
      "version": "1.19.10",
      "last_seen": "2021-08-18T07:57:55.96608Z"
    },
    {
      "instance_id": "0b086763-3eef-457b-85c3-72497e2194fa",
      "uname": "linux Ubuntu 18.04.5 LTS (Bionic Beaver) x86_64 QEMU Virtual CPU version 2.5+",
      "containerized": "True",
      "type": "plus",
      "version": "1.19.10",
      "last_seen": "2021-08-18T07:57:57.842124Z"
    },
    {
      "instance_id": "c891eebe-4def-459e-bb29-eb715e7846a8",
      "uname": "linux Ubuntu 18.04.5 LTS (Bionic Beaver) x86_64 QEMU Virtual CPU version 2.5+",
      "containerized": "False",
      "type": "plus",
      "version": "1.19.10",
      "last_seen": "2021-08-12T10:32:12.572133Z"
    }
  ]
}
```

BIG-IQ

```
$ curl -s http://counter.nginx.ff.lan/instances | jq
{
  "instances": [
    {
      "bigip": "2"
    }
  ],
  "details": [
    {
      "product": "BIG-IP",
      "version": "16.1.0",
      "edition": "Final",
      "build": "0.0.19",
      "isVirtual": "True",
      "isClustered": "False",
      "platformMarketingName": "BIG-IP Virtual Edition",
      "restFrameworkVersion": "16.1.0-0.0.19"
    },
    {
      "product": "BIG-IP",
      "version": "16.1.0",
      "edition": "Final",
      "build": "0.0.19",
      "isVirtual": "True",
      "isClustered": "False",
      "platformMarketingName": "BIG-IP Virtual Edition",
      "restFrameworkVersion": "16.1.0-0.0.19"
    }
  ]
}
```

Prometheus endpoint:

Pulling from NGINX Instance Manager

```
$ curl -s http://counter.nginx.ff.lan/metrics
# HELP nginx_oss_online_instances Online NGINX OSS instances
# TYPE nginx_oss_online_instances gauge
nginx_oss_online_instances{subscription="NGX-Subscription-1-TRL-064788",instanceType="INSTANCE_MANAGER",instanceVersion="1.0.2",instanceSerial="6232847160738694"} 1
# HELP nginx_plus_online_instances Online NGINX Plus instances
# TYPE nginx_plus_online_instances gauge
nginx_plus_online_instances{subscription="NGX-Subscription-1-TRL-064788",instanceType="INSTANCE_MANAGER",instanceVersion="1.0.2",instanceSerial="6232847160738694"} 0
```

Pulling from NGINX Controller

```
$ curl -s http://counter.nginx.ff.lan/metrics
# HELP nginx_plus_online_instances Online NGINX Plus instances
# TYPE nginx_plus_online_instances gauge
nginx_plus_online_instances{subscription="NGX-Subscription-1-TRL-046027",instanceType="NGINX Controller",instanceVersion="3.18.2",location="test"} 0
# HELP nginx_plus_offline_instances Offline NGINX Plus instances
# TYPE nginx_plus_offline_instances gauge
nginx_plus_offline_instances{subscription="NGX-Subscription-1-TRL-046027",instanceType="NGINX Controller",instanceVersion="3.18.2",location="test"} 0
# HELP nginx_plus_online_instances Online NGINX Plus instances
# TYPE nginx_plus_online_instances gauge
nginx_plus_online_instances{subscription="NGX-Subscription-1-TRL-046027",instanceType="NGINX Controller",instanceVersion="3.18.2",location="unspecified"} 2
# HELP nginx_plus_offline_instances Offline NGINX Plus instances
# TYPE nginx_plus_offline_instances gauge
nginx_plus_offline_instances{subscription="NGX-Subscription-1-TRL-046027",instanceType="NGINX Controller",instanceVersion="3.18.2",location="unspecified"} 283
```

Pulling from BIG-IQ

```
$ curl -s https://counter.nginx.ff.lan/metrics
# HELP bigip_online_instances Online BIG-IP instances
# TYPE bigip_online_instances gauge
bigip_online_instances{instanceType="BIG-IQ",bigiq_url="https://10.155.153.208:443"} 2
```

## Push mode to custom URL

Sample unauthenticated POST payload:

```
POST /callHome HTTP/1.1
Host: 192.168.1.18
User-Agent: python-requests/2.22.0
Accept-Encoding: gzip, deflate
Accept: */*
Connection: keep-alive
Content-Type: application/json
Content-Length: 267

{
  "subscription": {
    "id": "NGX-Subscription-1-TRL-XXXXXX",
    "type": "INSTANCE_MANAGER",
    "version": "1.0.2",
    "serial": "6232847160738694"
  },
  "instances": [
    {
      "nginx_plus_online": 0,
      "nginx_oss_online": 1
    }
  ],
  "details": [
    {
      "instance_id": "ee3f2f76-aa22-4182-b643-ba298cc0f758",
      "uname": "Linux ubuntu 5.4.0-80-generic #90-Ubuntu SMP Fri Jul 9 22:49:44 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux",
      "containerized": "False",
      "type": "oss",
      "version": "1.18.0",
      "last_seen": "2021-08-18T07:57:11.670746604Z"
    }
  ]
}
```

Sample POST payload with Basic Authentication

```
POST /callHome HTTP/1.1
Host: 192.168.1.18
User-Agent: python-requests/2.22.0
Accept-Encoding: gzip, deflate
Accept: */*
Connection: keep-alive
Content-Type: application/json
Content-Length: 267
Authorization: Basic YWE6YmI=

{
  "subscription": {
    "id": "NGX-Subscription-1-TRL-XXXXXX",
    "type": "INSTANCE_MANAGER",
    "version": "1.0.2",
    "serial": "6232847160738694"
  },
  "instances": [
    {
      "nginx_plus_online": 0,
      "nginx_oss_online": 1
    }
  ],
  "details": [
    {
      "instance_id": "ee3f2f76-aa22-4182-b643-ba298cc0f758",
      "uname": "Linux ubuntu 5.4.0-80-generic #90-Ubuntu SMP Fri Jul 9 22:49:44 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux",
      "containerized": "False",
      "type": "oss",
      "version": "1.18.0",
      "last_seen": "2021-08-18T07:57:11.670746604Z"
    }
  ]
}
```


# Visualization

<img src="./images/grafana.1.jpg"/>

<img src="./images/grafana.2.jpg"/>
