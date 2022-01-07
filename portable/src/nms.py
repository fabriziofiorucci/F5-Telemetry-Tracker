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

this = sys.modules[__name__]

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

this.nms_fqdn=''
this.nms_username=''
this.nms_password=''
this.nms_proxy={}

# Module initialization
def init(fqdn,username,password,proxy,nistApiKey):
  this.nms_fqdn=fqdn
  this.nms_username=username
  this.nms_password=password
  this.nms_proxy=proxy

  cveDB.init(nistApiKey=nistApiKey,proxy=proxy)


### NGINX Management System REST API

def nmsRESTCall(method,uri):
  s = Session()
  req = Request(method,this.nms_fqdn+uri,auth=(this.nms_username,this.nms_password))

  p = s.prepare_request(req)
  s.proxies = this.nms_proxy
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


### NGINX Management System query functions

# Returns NGINX OSS/Plus instances managed by NMS in JSON format
def nmsInstances(mode):
  # Fetching NMS license
  status,license = nmsRESTCall(method='GET',uri='/api/platform/v1/license')

  if status != 200:
    return make_response({'error': 'fetching license failed'},status)

  # Fetching NMS system information
  status,system = nmsRESTCall(method='GET',uri='/api/platform/v1/systems')

  if status != 200:
    return make_response({'error': 'fetching systems information failed'},status)

  subscriptionId=license['currentStatus']['subscription']['id']
  instanceType=license['currentStatus']['state']['currentInstance']['features'][0]['id']
  instanceVersion=license['currentStatus']['state']['currentInstance']['version']
  instanceSerial=license['currentStatus']['state']['currentInstance']['id']
  totalManaged=len(system['items'])

  plusManaged=0
  for i in system['items']:
    if i['nginxInstances'][0]['build']['nginxPlus'] == True:
      plusManaged+=1

  output=''

  if mode == 'JSON':
    subscriptionDict = {}
    subscriptionDict['id'] = subscriptionId
    subscriptionDict['type'] = instanceType
    subscriptionDict['version'] = instanceVersion
    subscriptionDict['serial'] = instanceSerial

    instancesDict = {}
    instancesDict['nginx_plus_online'] = plusManaged
    instancesDict['nginx_oss_online'] = int(totalManaged)-int(plusManaged)

    output = {}
    output['subscription'] = subscriptionDict
    output['instances'] = instancesDict
    output['details'] = []


    for i in system['items']:
      systemId=i['uid']

      # Fetch system details
      status,systemDetails = nmsRESTCall(method='GET',uri='/api/platform/v1/systems/'+systemId+'?showDetails=true')
      if status != 200:
        return make_response({'error': 'fetching system details failed for '+systemId},status)

      for instance in i['nginxInstances']:
        # Fetch instance details
        status,instanceDetails = nmsRESTCall(method='GET',uri='/api/platform/v1/systems/'+systemId+'/instances/'+instance['uid'])
        if status != 200:
          return make_response({'error': 'fetching instance details failed for '+systemId+' / '+instance['uid']},status)

        # Fetch CVEs
        allCVE=cveDB.getNGINX(version=instanceDetails['build']['version'])

        detailsDict = {}
        detailsDict['instance_id'] = instance['uid']
        detailsDict['osInfo'] = systemDetails['osRelease']
        detailsDict['hypervisor'] = systemDetails['processor'][0]['hypervisor']
        if instanceDetails['build']['nginxPlus'] == False:
          detailsDict['type'] = "oss"
        else:
          detailsDict['type'] = "plus"
        detailsDict['version'] = instanceDetails['build']['version']
        detailsDict['last_seen'] = instance['status']['lastStatusReport']
        detailsDict['createtime'] = instance['startTime']
        detailsDict['modules'] = instanceDetails['loadableModules']
        detailsDict['networkconfig'] = {}
        detailsDict['networkconfig']['networkInterfaces'] = systemDetails['networkInterfaces']
        detailsDict['hostname'] = systemDetails['hostname']
        detailsDict['name'] = systemDetails['displayName']
        detailsDict['CVE'] = []
        detailsDict['CVE'].append(allCVE)

      output['details'].append(detailsDict)

    output = str(json.dumps(output))

  elif mode == 'PROMETHEUS' or mode == 'PUSHGATEWAY':
    if mode == 'PROMETHEUS':
      output = '# HELP nginx_oss_online_instances Online NGINX OSS instances\n'
      output = output + '# TYPE nginx_oss_online_instances gauge\n'

    output = output + 'nginx_oss_online_instances{subscription="'+subscriptionId+'",instanceType="'+instanceType+'",instanceVersion="'+instanceVersion+'",instanceSerial="'+instanceSerial+'"} '+str(int(totalManaged)-int(plusManaged))+'\n'

    if mode == 'PROMETHEUS':
      output = output + '# HELP nginx_plus_online_instances Online NGINX Plus instances\n'
      output = output + '# TYPE nginx_plus_online_instances gauge\n'

    output = output + 'nginx_plus_online_instances{subscription="'+subscriptionId+'",instanceType="'+instanceType+'",instanceVersion="'+instanceVersion+'",instanceSerial="'+instanceSerial+'"} '+str(plusManaged)+'\n'

  return output
