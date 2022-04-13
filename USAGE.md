# Usage

## REST API mode

For `/instances` and `/f5tt/instances` endpoints if the request includes the `Accept-Encoding: gzip` header the response will be compressed
The `/` endpoint displays a basic HTML view of generated JSON files

To get instance statistics in JSON format:

### NGINX Instance Manager 1.x

- Retrieve the full JSON: `curl -s http://f5tt.ff.lan/instances | jq`
- Browser mode: `http://f5tt.ff.lan`

### NGINX Instance Manager 2.x

the `type` query string parameter can be used to retrieve a logical view of the full JSON file:

- Browser mode: `http://f5tt.ff.lan` and `http://f5tt.ff.lan?type=CVE`
- Retrieve the full JSON: `curl -s http://f5tt.ff.lan/instances | jq`
- Retrieve the CVE-centric JSON: `curl -s http://f5tt.ff.lan/instances?type=CVE | jq`
- Retrieve the time-based usage JSON (N = aggregation based on N-hours timeslots): `curl -s http://f5tt.ff.lan/instances?type=timebased&month=M&slot=N | jq`
```
M = 0 to get time-based usage for the current month, -1 for previous month (defaults to -1 if not specified)
N = Aggregation based on N-hours timeslot (defaults to 4 is not specified)
```


### NGINX Controller

- Retrieve the full JSON: `curl -s http://f5tt.ff.lan/instances | jq`

- Browser mode: `http://f5tt.ff.lan`

### BIG-IQ

the `type` query string parameter can be used to retrieve a logical view of the full JSON file:

- Retrieve the standard full JSON: `curl -s http://f5tt.ff.lan/instances | jq`
- Retrieve a CVE-centric JSON: `curl -s http://f5tt.ff.lan/instances?type=CVE | jq`
- Retrieve the "Software on Hardware" JSON: `curl -s http://f5tt.ff.lan/instances?type=SwOnHw | jq`

- Browser mode: `http://f5tt.ff.lan`, `http://f5tt.ff.lan?type=CVE` and `http://f5tt.ff.lan?type=SwOnHw`


A dynamically updated report in xls format can be downloaded by accessing either:

- `curl -s http://f5tt.ff.lan/reporting/xls`
- `curl -s http://f5tt.ff.lan/f5tt/reporting/xls`

### Prometheus endpoint:

Pulling from NGINX Instance Manager

```
$ curl -s http://f5tt.ff.lan/metrics
# HELP nginx_oss_online_instances Online NGINX OSS instances
# TYPE nginx_oss_online_instances gauge
nginx_oss_online_instances{subscription="NGX-Subscription-1-TRL-064788",instanceType="INSTANCE_MANAGER",instanceVersion="1.0.2",instanceSerial="6232847160738694"} 1
# HELP nginx_plus_online_instances Online NGINX Plus instances
# TYPE nginx_plus_online_instances gauge
nginx_plus_online_instances{subscription="NGX-Subscription-1-TRL-064788",instanceType="INSTANCE_MANAGER",instanceVersion="1.0.2",instanceSerial="6232847160738694"} 0
```

Pulling from NGINX Controller

```
$ curl -s http://f5tt.ff.lan/metrics
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
$ curl -s https://f5tt.ff.lan/metrics
# HELP bigip_online_instances Online BIG-IP instances
# TYPE bigip_online_instances gauge
bigip_online_instances{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan"} 2
# HELP bigip_hwTotals Total hardware devices count
# TYPE bigip_hwtotals gauge
bigip_hwtotals{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",bigip_sku="F5-VE"} 1
# HELP bigip_swTotals Total software modules count
# TYPE bigip_swtotals gauge
bigip_swtotals{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",bigip_module="H-VE-APM"} 1
bigip_swtotals{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",bigip_module="H-VE-DNS"} 1
bigip_swtotals{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",bigip_module="H-VE-LTM"} 1
bigip_swtotals{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",bigip_module="H-VE-CGNAT"} 1
# HELP bigip_tmos_releases TMOS releases count
# TYPE bigip_tmos_releases gauge
bigip_tmos_releases{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_release="16.1.0"} 2
# HELP bigip_tmos_cve TMOS CVE count
# TYPE bigip_tmos_cve gauge
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23019"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23021"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23032"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23022"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23020"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23016"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23014"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23030"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23025"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2022-23023"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2021-23037"} 1
bigip_tmos_cve{dataplane_type="BIG-IQ",dataplane_url="https://bigiq.f5.ff.lan",tmos_cve="CVE-2021-23043"} 1
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
  ...
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
  ...
}
```


## Visualization

See [Grafana](/contrib/grafana)


## Sample report e-mail

<img src="./images/reporting-mail.png"/>
