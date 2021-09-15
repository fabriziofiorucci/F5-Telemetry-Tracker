#!/usr/bin/python3

## #!flask/bin/python
from flask import Flask, jsonify, abort, make_response, request
import os
import sys
import ssl
import json
import sched,time,datetime
import requests
import time
import threading
from requests import Request, Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

sessionCookie = ''
nc_mode=os.environ['NGINX_CONTROLLER_TYPE']
nc_fqdn=os.environ['NGINX_CONTROLLER_FQDN']
nc_user=os.environ['NGINX_CONTROLLER_USERNAME']
nc_pass=os.environ['NGINX_CONTROLLER_PASSWORD']


# Scheduler for automated statistics push / call home
def scheduledPush(url,username,password,interval,pushmode):
  counter = 0

  pushgatewayUrl=url+"/metrics/job/nginx-instance-counter"

  while (counter>=0):
    try:
      if nc_mode == 'NGINX_CONTROLLER':
        if pushmode == 'CUSTOM':
          payload=ncInstances(mode='JSON')
        elif pushmode == 'NGINX_PUSH':
          payload=ncInstances(mode='PUSHGATEWAY')
      elif nc_mode == 'NGINX_INSTANCE_MANAGER':
        if pushmode == 'CUSTOM':
          payload=nimInstances(mode='JSON')
        elif pushmode == 'NGINX_PUSH':
          payload=nimInstances(mode='PUSHGATEWAY')
      elif nc_mode == 'BIG_IQ':
        if pushmode == 'CUSTOM':
          payload=bigIqInventory(mode='JSON')
        elif pushmode == 'NGINX_PUSH':
          payload=bigIqInventory(mode='PUSHGATEWAY')

      try:
        if username == '' or password == '':
          if pushmode == 'CUSTOM':
            # Push json to custom URL
            r = requests.post(url, data=payload, headers={'Content-Type': 'application/json'}, timeout=10)
          elif pushmode == 'NGINX_PUSH':
            # Push to pushgateway
            r = requests.post(pushgatewayUrl, data=payload, timeout=10)
        else:
          if pushmode == 'CUSTOM':
            # Push json to custom URL with basic auth
            r = requests.post(url, auth=(username,password), data=payload, headers={'Content-Type': 'application/json'}, timeout=10)
          elif pushmode == 'NGINX_PUSH':
            # Push to pushgateway
            r = requests.post(pushgatewayUrl, auth=(username,password), data=payload, timeout=10)
      except:
        e = sys.exc_info()[0]
        print(datetime.datetime.now(),counter,'Pushing stats to',url,'failed:',e)
      else:
        print(datetime.datetime.now(),counter,'Pushing stats to',url,'returncode',r.status_code)

    except:
      print('Exception caught during push')

    counter = counter + 1

    time.sleep(interval)


### NGINX Controller REST API

# NGINX Controller - login
# Returns the session cookie
def nginxControllerLogin(fqdn,username,password):
  data = ('{"credentials":{"type": "BASIC","username": "'+username+'","password": "'+password+'"}}')
  headers = { 'Content-Type': 'application/json' }

  s = Session()
  req = Request('POST',fqdn+"/api/v1/platform/login",data=data,headers=headers)

  p = s.prepare_request(req)
  res = s.send(p,verify=False)

  if res.status_code == 204:
    sessionCookie = res.headers['set-cookie'].split(" ", 1)[0].split(";")[0]
  else:
    sessionCookie = ''

  return res.status_code,sessionCookie


# NGINX Controller - logout
# Invalidates the session cookie
def nginxControllerLogout(fqdn,cookie):
  s = Session()
  req = Request('POST',fqdn+"/api/v1/platform/logout")

  p = s.prepare_request(req)
  p.headers['Cookie']=cookie
  res = s.send(p,verify=False)

  return res.status_code


# Returns NGINX Controller license information
def nginxControllerLicense(fqdn,cookie):
  s = Session()
  req = Request('GET',fqdn+"/api/v1/platform/license")

  p = s.prepare_request(req)
  p.headers['Cookie']=cookie
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


# Returns HTTP status (200/401) and NGINX Controller locations
def nginxControllerLocations(fqdn,cookie):
  s = Session()
  req = Request('GET',fqdn+"/api/v1/infrastructure/locations")

  p = s.prepare_request(req)
  p.headers['Cookie']=cookie
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


# Returns HTTP status (200/401) and NGINX Plus instances for the given NGINX Controller location
def nginxControllerInstances(fqdn,cookie,location):
  s = Session()
  req = Request('GET',fqdn+"/api/v1/infrastructure/locations/"+location+"/instances")

  p = s.prepare_request(req)
  p.headers['Cookie']=cookie
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


### NGINX Instance Manager REST API

# Returns NIM Controller license information
def nginxInstanceManagerLicense(fqdn):
  s = Session()
  req = Request('GET',fqdn+"/api/v0/about/license")

  p = s.prepare_request(req)
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data

# Returns NIM Controller system information
def nginxInstanceManagerSystem(fqdn):
  s = Session()
  req = Request('GET',fqdn+"/api/v0/about/system")

  p = s.prepare_request(req)
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


# Returns NGINX OSS/Plus instances managed by NIM
def nginxInstanceManagerInstances(fqdn):
  s = Session()
  req = Request('GET',fqdn+"/api/v0/instances")

  p = s.prepare_request(req)
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


### BIG-IQ REST API

# Returns NGINX OSS/Plus instances managed by NIM
def bigIQInstances(fqdn):
  res = requests.request("GET", fqdn+"/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices", auth=(nc_user,nc_pass), verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


### NGINX Controller query functions

# Returns NGINX Plus instances managed by NGINX Controller in JSON format
def ncInstances(mode):
  # NGINX Controller login
  status,sessionCookie = nginxControllerLogin(nc_fqdn,nc_user,nc_pass)
  if status != 204:
    return make_response(jsonify({'error': 'authentication failed'}), 401)

  # Fetches controller license
  status,license = nginxControllerLicense(nc_fqdn,sessionCookie)
  if status != 200:
    return make_response(jsonify({'error': 'fetching license failed'}), 401)

  subscriptionId=license['currentStatus']['subscription']['id']
  instanceType=license['currentStatus']['state']['currentInstance']['type']
  instanceVersion=license['currentStatus']['state']['currentInstance']['version']

  # Fetches locations
  status,locations = nginxControllerLocations(nc_fqdn,sessionCookie)
  if status != 200:
    return make_response(jsonify({'error': 'locations fetch error'}), 404)

  if mode == 'JSON':
    output = '{ "subscription": {"id": "'+subscriptionId+'","type":"'+instanceType+'","version":"'+instanceVersion+'"},"instances": ['
    firstLoop = True
  else:
    output = ''

  firstILoop = True
  instanceDetails = ''

  # Iterates locations
  for l in locations['items']:
    if mode == 'JSON':
      if firstLoop == True :
        firstLoop=False
      else:
        output+=','

    locName = l['metadata']['name']

    # Iterates and counts online instances
    status,instances = nginxControllerInstances(nc_fqdn,sessionCookie,locName)
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
        if firstILoop == True :
          firstILoop = False
        else:
          instanceDetails = instanceDetails + ','

        # Retrieves instance details
        lsm = i['currentStatus']['legacySystemMetadata']
        uname = lsm['os-type']+' '+lsm['release']['name']+ ' '+lsm['release']['version']+' '+lsm['processor']['architecture']+' '+lsm['processor']['model']

        if lsm['processor']['hypervisor'] == 'container':
          containerized = "True"
        else:
          containerized = "False"

        instanceDetails = instanceDetails + '{' + \
          '"instance_id":"' + i['metadata']['uid'] + '",' + \
          '"uname":"' + uname + '",' + \
          '"containerized":"' + containerized + '",' + \
          '"type":"' + 'plus' + '",' + \
          '"version":"' + i['currentStatus']['version'] + '",' + \
          '"last_seen":"' + i['currentStatus']['legacyNginxMetadata']['last_seen'] + '",' + \
          '"createtime":"' + i['metadata']['createTime'] + '",' + \
          '"networkConfig":' + str(i['currentStatus']['networkConfig']).replace('\'','"') + ',' + \
          '"hostname":"' + i['currentStatus']['hostname'] + '"' + \
          '}'

    if mode == 'JSON':
      output = output + '{"location": "'+locName+'", "nginx_plus_online": '+str(online)+', "nginx_plus_offline": '+str(offline)+'}'
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
    output = output + '], "details": [' + instanceDetails + ']}'

  nginxControllerLogout(nc_fqdn,sessionCookie)

  return output


### NGINX Instance Manager query functions

# Returns NGINX OSS/Plus instances managed by NIM in JSON format
def nimInstances(mode):
  # Fetching NIM license
  status,license = nginxInstanceManagerLicense(nc_fqdn)
  if status != 200:
    return make_response(jsonify({'error': 'fetching license failed'}), 401)

  # Fetching NIM system information
  status,system = nginxInstanceManagerSystem(nc_fqdn)
  if status != 200:
    return make_response(jsonify({'error': 'fetching system information failed'}), 401)

  subscriptionId=license['attributes']['subscription']
  instanceType=license['licenses'][0]['product_code']
  instanceVersion=system['version']
  instanceSerial=license['licenses'][0]['serial']
  plusManaged=license['plus_instances_managed']
  totalManaged=license['total_instances_managed']

  # Fetching instances
  status,instances = nginxInstanceManagerInstances(nc_fqdn)

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

      output = output + '{ \
        "instance_id": "'+i['instance_id'] + '", \
        "uname": "'+i['uname'] + '", \
        "containerized": "'+str(i['containerized']) + '", \
        "type": "'+i['nginx']['type'] + '", \
        "version": "'+i['nginx']['version'] + '", \
        "last_seen": "'+i['lastseen']+'", \
        "createtime": "'+i['added']+'", \
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


### BIG-IQ query functions

# Returns NGINX OSS/Plus instances managed by BIG-IQ in JSON format
def bigIqInventory(mode):

  status,details = bigIQInstances(nc_fqdn)
  if status != 200:
    return make_response(jsonify({'error': 'fetching instances failed'}), 401)

  output=''

  if mode == 'JSON':
    output = '{ "instances": [{ "bigip":"'+str(len(details['items']))+'"}], "details": ['
    firstLoop = True

    for item in details['items']:
      if mode == 'JSON':
        if firstLoop == True :
          firstLoop=False
        else:
          output+=','

        output += '{"product":"'+item['product']+'","version":"'+item['version']+'","edition":"'+ \
          item['edition']+'","build":"'+item['build']+'","isVirtual":"'+str(item['isVirtual'])+'","isClustered":"'+str(item['isClustered'])+ \
          '","platformMarketingName":"'+item['platformMarketingName']+'","restFrameworkVersion":"'+ \
          item['restFrameworkVersion']+'"}'

    output = output + ']}'
  elif mode == 'PROMETHEUS' or mode == 'PUSHGATEWAY':
    if mode == 'PROMETHEUS':
      output = '# HELP bigip_online_instances Online BIG-IP instances\n'
      output = output + '# TYPE bigip_online_instances gauge\n'

    output = output + 'bigip_online_instances{instanceType="BIG-IQ",bigiq_url="'+nc_fqdn+'"} '+str(len(details['items']))+'\n'

  return output


# Returns stats in json format
@app.route('/instances', methods=['GET'])
def getInstances():
  if nc_mode == 'NGINX_CONTROLLER':
    return ncInstances(mode='JSON')
  elif nc_mode == 'NGINX_INSTANCE_MANAGER':
    return nimInstances(mode='JSON')
  elif nc_mode == 'BIG_IQ':
    return bigIqInventory(mode='JSON')


# Returns stats in prometheus format
@app.route('/metrics', methods=['GET'])
def getMetrics():
  if nc_mode == 'NGINX_CONTROLLER':
    return ncInstances(mode='PROMETHEUS')
  elif nc_mode == 'NGINX_INSTANCE_MANAGER':
    return nimInstances(mode='PROMETHEUS')
  elif nc_mode == 'BIG_IQ':
    return bigIqInventory(mode='PROMETHEUS')


@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':

  if nc_mode != 'NGINX_CONTROLLER' and nc_mode != 'NGINX_INSTANCE_MANAGER' and nc_mode != 'BIG_IQ' :
    print('Invalid NGINX_CONTROLLER_TYPE')
  else:
    # Push thread
    if os.environ['STATS_PUSH_ENABLE'] == 'true':
      stats_push_mode=os.environ['STATS_PUSH_MODE']

      if stats_push_mode != 'NGINX_PUSH' and stats_push_mode != 'CUSTOM':
        print('Invalid STATS_PUSH_MODE')
      else:
        stats_push_url=os.environ['STATS_PUSH_URL']
        if "STATS_PUSH_USERNAME" in os.environ:
          stats_push_username=os.environ['STATS_PUSH_USERNAME']
        else:
          stats_push_username=''

        if "STATS_PUSH_PASSWORD" in os.environ:
          stats_push_password=os.environ['STATS_PUSH_PASSWORD']
        else:
          stats_push_password=''

        stats_push_interval=int(os.environ['STATS_PUSH_INTERVAL'])

        print('Pushing stats to',stats_push_url,'every',stats_push_interval,'seconds')

        print('Running push thread')
        pushThread = threading.Thread(target=scheduledPush,args=(stats_push_url,stats_push_username,stats_push_password,stats_push_interval,stats_push_mode))
        pushThread.start()

    # REST API / prometheus metrics server
    print('Running REST API/Prometheus metrics server')
    app.run(host='0.0.0.0')

