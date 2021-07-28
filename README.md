# NGINX Instance Counter

## Description

This is a simple microservice that helps tracking NGINX Plus instances managed by NGINX Controller and NGINX Instance Manager

It has been tested against:

- NGINX Controller 3.18
- NGINX Instance Manager 1.0.1

Communication to NGINX Controller / NGINX Instance Manager is based on REST API, and two kinds of output are supported:

- JSON
- prometheus "metrics" format

## Prerequisites

- Kubernetes or Openshift cluster
- Private registry to push the NGINX Instance Counter image
- NGINX Controller 3.18 or NGINX Instance Manager 1.0.1

## How to build

The NGINX Instance Counter image is available on docker as:

```
fiorucci/nginx-instance-counter:1.0
```

The 0.instancecounter.yaml references that by default.

If you need to build and push NGINX your own image to a private registry:

```
git clone fabriziofiorucci/NGINX-InstanceCounter
cd NGINX-InstanceCounter/nginx-instance-counter

docker build --no-cache -t PRIVATE_REGISTRY:PORT/nginx-instance-counter:1.0 .
docker push PRIVATE_REGISTRY:PORT/nginx-instance-counter:1.0
```

## How to deploy

```
cd NGINX-InstanceCounter
```

Edit 0.instancecounter.yaml to customize:

- image name:
  - To be set to your private registry image
- environment variables:
  - NGINX_CONTROLLER_FQDN - the FQDN[:port] of your NGINX Controller / NGINX Instance Manager instance
  - NGINX_CONTROLLER_USERNAME - the username for NGINX Controller authentication
  - NGINX_CONTROLLER_PASSWORD - the password for NGINX Controller authentication
  - NGINX_CONTROLLER_TYPE - either NGINX_CONTROLLER or NGINX_INSTANCE_MANAGER
- Ingress host:
  - By default it is set to counter.nginx.ff.lan

```
kubectl apply -f 0.instancecounter.yaml
```

## Usage

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
