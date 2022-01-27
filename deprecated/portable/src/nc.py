import flask
from flask import Flask, jsonify, abort, make_response, request, Response
import os
import sys
import ssl
import json
import sched,time,datetime
import requests
import time
import threading
import smtplib
import urllib3.exceptions
import base64
from requests import Request, Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from email.message import EmailMessage

import cveDB

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

### NGINX Controller REST API

# NGINX Controller - login
# Returns the session cookie
def nginxControllerLogin(fqdn,username,password,proxy):
  data = ('{"credentials":{"type": "BASIC","username": "'+username+'","password": "'+password+'"}}')
  headers = { 'Content-Type': 'application/json' }

  s = Session()
  req = Request('POST',fqdn+"/api/v1/platform/login",data=data,headers=headers)

  p = s.prepare_request(req)
  s.proxies = proxy
  res = s.send(p,verify=False)

  if res.status_code == 204:
    sessionCookie = res.headers['set-cookie'].split(" ", 1)[0].split(";")[0]
  else:
    sessionCookie = ''

  return res.status_code,sessionCookie


# NGINX Controller - logout
# Invalidates the session cookie
def nginxControllerLogout(fqdn,cookie,proxy):
  s = Session()
  req = Request('POST',fqdn+"/api/v1/platform/logout")

  p = s.prepare_request(req)
  s.proxies = proxy
  p.headers['Cookie']=cookie
  res = s.send(p,verify=False)

  return res.status_code


# Returns NGINX Controller license information
def nginxControllerLicense(fqdn,cookie,proxy):
  s = Session()
  req = Request('GET',fqdn+"/api/v1/platform/license")

  p = s.prepare_request(req)
  s.proxies = proxy
  p.headers['Cookie']=cookie
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


# Returns HTTP status (200/401) and NGINX Controller locations
def nginxControllerLocations(fqdn,cookie,proxy):
  s = Session()
  req = Request('GET',fqdn+"/api/v1/infrastructure/locations")

  p = s.prepare_request(req)
  s.proxies = proxy
  p.headers['Cookie']=cookie
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


# Returns HTTP status (200/401) and NGINX Plus instances for the given NGINX Controller location
def nginxControllerInstances(fqdn,cookie,location,proxy):
  s = Session()
  req = Request('GET',fqdn+"/api/v1/infrastructure/locations/"+location+"/instances")

  p = s.prepare_request(req)
  p.headers['Cookie']=cookie
  s.proxies = proxy
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


### NGINX Controller query functions

# Returns NGINX Plus instances managed by NGINX Controller in JSON format
def ncInstances(fqdn,username,password,mode,proxy):
  # NGINX Controller login
  status,sessionCookie = nginxControllerLogin(fqdn,username,password,proxy)
  if status != 204:
    return make_response(jsonify({'error': 'authentication failed'}), 401)

  # Fetches controller license
  status,license = nginxControllerLicense(fqdn,sessionCookie,proxy)
  if status != 200:
    return make_response(jsonify({'error': 'fetching license failed'}), 401)

  subscriptionId=license['currentStatus']['subscription']['id']
  instanceType=license['currentStatus']['state']['currentInstance']['type']
  instanceVersion=license['currentStatus']['state']['currentInstance']['version']

  # Fetches ocations
  status,locations = nginxControllerLocations(fqdn,sessionCookie,proxy)
  if status != 200:
    return make_response(jsonify({'error': 'locations fetch error'}), 404)

  if mode == 'JSON':
    subscriptionDict = {}
    subscriptionDict['id'] = subscriptionId
    subscriptionDict['type'] = instanceType
    subscriptionDict['version'] = instanceVersion
  else:
    output = ''

  allDetailsDict = []
  instancesDict = []

  # Iterates locations
  for l in locations['items']:
    locName = l['metadata']['name']

    # Iterates and counts online instances
    status,instances = nginxControllerInstances(fqdn,sessionCookie,locName,proxy)
    if status != 200:
      return make_response(jsonify({'error': 'instances fetch error'}), 404)

    online = 0
    offline = 0
    for i in instances['items']:
      if i['currentStatus']['agent']['online'] == True:
        online+=1
      else:
        offline+=1

      if mode == 'JSON':
        # Retrieves instance details
        lsm = i['currentStatus']['legacySystemMetadata']
        uname = lsm['os-type']+' '+lsm['release']['name']+ ' '+lsm['release']['version']+' '+lsm['processor']['architecture']+' '+lsm['processor']['model']

        if lsm['processor']['hypervisor'] == 'container':
          containerized = True
        else:
          containerized = False

        # CVE tracking
        allCVE=cveDB.getNGINX(version=i['currentStatus']['version'])

        detailsDict = {}
        detailsDict['instance_id'] = i['metadata']['uid']
        detailsDict['uname'] = uname
        detailsDict['containerized'] = containerized
        detailsDict['type'] = "plus"
        detailsDict['version'] = i['currentStatus']['version']
        detailsDict['last_seen'] = i['currentStatus']['legacyNginxMetadata']['last_seen']
        detailsDict['createtime'] = i['metadata']['createTime']
        detailsDict['networkConfig'] = i['currentStatus']['networkConfig']
        detailsDict['hostname'] = i['currentStatus']['hostname']
        detailsDict['name'] = i['metadata']['name']
        detailsDict['CVE'] = []
        detailsDict['CVE'].append(allCVE)

        allDetailsDict.append(detailsDict)

    if mode == 'JSON':
      thisInstanceDict = {}
      thisInstanceDict['location'] = locName
      thisInstanceDict['nginx_plus_online'] = online
      thisInstanceDict['nginx_plus_offline'] = offline

      instancesDict.append(thisInstanceDict)
    elif mode == 'PROMETHEUS' or mode == 'PUSHGATEWAY':
      if mode == 'PROMETHEUS':
        output = output + '# HELP nginx_plus_online_instances Online NGINX Plus instances\n'
        output = output + '# TYPE nginx_plus_online_instances gauge\n'

      output = output + 'nginx_plus_online_instances{subscription="'+subscriptionId+'",instanceType="'+instanceType+'",instanceVersion="'+instanceVersion+'",location="'+locName+'"} '+str(online)+'\n'

      if mode == 'PROMETHEUS':
        output = output + '# HELP nginx_plus_offline_instances Offline NGINX Plus instances\n'
        output = output + '# TYPE nginx_plus_offline_instances gauge\n'

      output = output + 'nginx_plus_offline_instances{subscription="'+subscriptionId+'",instanceType="'+instanceType+'",instanceVersion="'+instanceVersion+'",location="'+locName+'"} '+str(offline)+'\n'

  if mode == 'JSON':
    output = {}
    output['subscription'] = subscriptionDict
    output['instances'] = instancesDict
    output['details'] = allDetailsDict

    output = str(json.dumps(output))

  nginxControllerLogout(fqdn,sessionCookie,proxy)

  return output
