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

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# NGINX dynamic modules
nginxModules = {
  "ngx_http_app_protect_module.so": "nap"
}


### NGINX Instance Manager REST API

def nginxInstanceManagerRESTCall(method,fqdn,uri,proxy):
  s = Session()
  req = Request(method,fqdn+uri)

  p = s.prepare_request(req)
  s.proxies = proxy
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


### NGINX Instance Manager query functions

# Returns NGINX OSS/Plus instances managed by NIM in JSON format
def nimInstances(fqdn,mode,proxy):
  # Fetching NIM license
  status,license = nginxInstanceManagerRESTCall(method='GET',fqdn=fqdn,uri='/api/v0/about/license',proxy=proxy)

  if status != 200:
    return make_response(jsonify({'error': 'fetching license failed'}), 401)

  # Fetching NIM system information
  status,system = nginxInstanceManagerRESTCall(method='GET',fqdn=fqdn,uri='/api/v0/about/system',proxy=proxy)
  if status != 200:
    return make_response(jsonify({'error': 'fetching system information failed'}), 401)

  subscriptionId=license['attributes']['subscription']
  instanceType=license['licenses'][0]['product_code']
  instanceVersion=system['version']
  instanceSerial=license['licenses'][0]['serial']
  plusManaged=license['plus_instances_managed']
  totalManaged=license['total_instances_managed']

  # Fetching instances
  status,instances = nginxInstanceManagerRESTCall(method='GET',fqdn=fqdn,uri='/api/v0/instances',proxy=proxy)

  if status != 200:
    return make_response(jsonify({'error': 'instances fetch error'}), 404)

  output=''

  if mode == 'JSON':
    output = '{ "subscription": {"id": "'+subscriptionId+'","type":"'+instanceType+'","version":"'+instanceVersion+'","serial":"'+instanceSerial+'"},' + \
             '"instances": [ {"nginx_plus_online": '+plusManaged+', "nginx_oss_online": '+str(int(totalManaged)-int(plusManaged)) + \
             '}],"details": ['

    firstLoop=True

    for i in instances['list']:

      if firstLoop == True :
        firstLoop=False
      else:
        output+=','

      # Parses /etc/nginx/nginx.conf to detect NGINX App Protect usage
      instanceId=i['instance_id']
      status,configFiles = nginxInstanceManagerRESTCall(method='GET',fqdn=fqdn,uri='/api/v0/instances/'+instanceId+'/config',proxy=proxy)

      nginxModulesJSON=''

      if status == 200:
        for configFile in configFiles['files']:
          if configFile['name'] == '/etc/nginx/nginx.conf':
            fileContent=str(base64.b64decode(configFile['contents']))

            # Looks for modules in nginxModules "load_module modules/MODULE_NAME;"
            mFirstLoop=True
            for module in nginxModules:
              modulePosition=fileContent.find(module)

              if modulePosition != -1:
                # Looks for line containing the module name
                previousCrPosition=fileContent.rfind('\\n',0,modulePosition)
                nextCrPosition=max(0,fileContent.find('\\n',modulePosition))
                moduleLine=fileContent[previousCrPosition:max(nextCrPosition,modulePosition+len(module))].replace('\\n','')

                # Checks that load_module is used and not commented out
                loadModulePosition=moduleLine.find('load_module')
                if loadModulePosition != -1:
                  if moduleLine.rfind('#',0,loadModulePosition) == -1:
                    if mFirstLoop == True :
                      mFirstLoop=False
                    else:
                      nginxModulesJSON+=','

                    nginxModulesJSON+='"'+nginxModules[module]+'":"enabled"'

      output = output + '{ \
        "instance_id": "' + instanceId + '", \
        "uname": "'+i['uname'] + '", \
        "containerized": "'+str(i['containerized']) + '", \
        "type": "'+i['nginx']['type'] + '", \
        "version": "'+i['nginx']['version'] + '", \
        "last_seen": "'+i['lastseen']+'", \
        "createtime": "'+i['added']+'", \
        "modules": {'+nginxModulesJSON+'}, \
        "networkconfig": { "host_ips": '+str(i['host_ips']).replace('\'','"')+'}, \
        "hostname": "'+i['hostname']+'" \
      }'

    output = output + ']}'
  elif mode == 'PROMETHEUS' or mode == 'PUSHGATEWAY':
    if mode == 'PROMETHEUS':
      output = '# HELP nginx_oss_online_instances Online NGINX OSS instances\n'
      output = output + '# TYPE nginx_oss_online_instances gauge\n'

    output = output + 'nginx_oss_online_instances{subscription="'+subscriptionId+'",instanceType="'+instanceType+'",instanceVersion="'+instanceVersion+'",instanceSerial="'+instanceSerial+'"} '+str(int(totalManaged)-int(plusManaged))+'\n'

    if mode == 'PROMETHEUS':
      output = output + '# HELP nginx_plus_online_instances Online NGINX Plus instances\n'
      output = output + '# TYPE nginx_plus_online_instances gauge\n'

    output = output + 'nginx_plus_online_instances{subscription="'+subscriptionId+'",instanceType="'+instanceType+'",instanceVersion="'+instanceVersion+'",instanceSerial="'+instanceSerial+'"} '+plusManaged+'\n'

  return output
