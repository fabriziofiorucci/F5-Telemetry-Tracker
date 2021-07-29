# NGINX Instance Counter

## Description

This microservice helps tracking NGINX Plus instances managed by NGINX Controller and NGINX Instance Manager

It has been tested against:

- NGINX Controller 3.18
- NGINX Instance Manager 1.0.1

Communication to NGINX Controller / NGINX Instance Manager is based on REST API, and two modes of operation are supported:

- REST API mode
  - /instances - returning JSON output
  - /metrics - returning prometheus compliant output
- Push mode
  - POSTs instances statistics to a user-defined HTTP(S) URL
  - Basic authentication support
  - User-defined push interval (in seconds)

## Prerequisites

- Kubernetes or Openshift cluster
- Private registry to push the NGINX Instance Counter image
- NGINX Controller 3.18 or NGINX Instance Manager 1.0.1

## How to build

The NGINX Instance Counter image is available on Docker Hub as:

```
fiorucci/nginx-instance-counter:1.2
```

The 1.instancecounter.yaml file references that by default.

If you need to build and push NGINX your own image to a private registry:

```
git clone fabriziofiorucci/NGINX-InstanceCounter
cd NGINX-InstanceCounter/nginx-instance-counter

docker build --no-cache -t PRIVATE_REGISTRY:PORT/nginx-instance-counter:1.2 .
docker push PRIVATE_REGISTRY:PORT/nginx-instance-counter:1.2
```

## How to deploy

```
cd NGINX-InstanceCounter
```

Edit 1.instancecounter.yaml to customize:

- image name:
  - To be set to your private registry image (only if not using the image available on Docker Hub)
- environment variables:
  - NGINX_CONTROLLER_TYPE - either NGINX_CONTROLLER or NGINX_INSTANCE_MANAGER
  - NGINX_CONTROLLER_FQDN - the FQDN of your NGINX Controller / NGINX Instance Manager instance - format must be http[s]://FQDN:port
  - NGINX_CONTROLLER_USERNAME - the username for NGINX Controller authentication
  - NGINX_CONTROLLER_PASSWORD - the password for NGINX Controller authentication

  - STATS_PUSH_ENABLE - if set to 'true' push mode is used instead of REST API
  - STATS_PUSH_URL - the URL where to POST instances statistics
  - STATS_PUSH_INTERVAL - the interval in seconds between two consecutive push
  - STATS_PUSH_USERNAME - (optional) the username for POST Basic Authentication
  - STATS_PUSH_PASSWORD - (optional) the password for POST Basic Authentication
- Ingress host:
  - By default it is set to counter.nginx.ff.lan

```
kubectl apply -f 0.ns.yaml
kubectl apply -f 1.instancecounter.yaml
```

## Usage - REST API mode

To get instance statistics in JSON format:

```
$ curl -s http://counter.nginx.ff.lan/instances | jq
[
  {
    "location": "test",
    "online": 0,
    "offline": 0
  },
  {
    "location": "unspecified",
    "online": 2,
    "offline": 5
  }
]
```

Prometheus endpoint:

```
$ curl -s http://counter.nginx.ff.lan/metrics
# HELP nginx_online_instances Online NGINX Plus instances
# TYPE nginx_online_instances gauge
nginx_online_instances{location="test"} 0
# HELP nginx_offline_instances Offline NGINX Plus instances
# TYPE nginx_offline_instances gauge
nginx_offline_instances{location="test"} 0
# HELP nginx_online_instances Online NGINX Plus instances
# TYPE nginx_online_instances gauge
nginx_online_instances{location="unspecified"} 2
# HELP nginx_offline_instances Offline NGINX Plus instances
# TYPE nginx_offline_instances gauge
nginx_offline_instances{location="unspecified"} 5
```

## Usage - Push mode

Sample unauthenticated POST payload:

```
POST /callHome HTTP/1.1
Host: 192.168.1.18
User-Agent: python-requests/2.22.0
Accept-Encoding: gzip, deflate
Accept: */*
Connection: keep-alive
Content-Type: application/json
Content-Length: 104

[{"location": "test", "online": 0, "offline": 0},{"location": "unspecified", "online": 2, "offline": 5}]
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
Content-Length: 104
Authorization: Basic YWFhOmJiYg==

[{"location": "test", "online": 0, "offline": 0},{"location": "unspecified", "online": 2, "offline": 5}]
```


## Visualization with Prometheus and Grafana

Work in progress, coming soon
