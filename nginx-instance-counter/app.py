#!/usr/bin/python3

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

app = Flask(__name__)

sessionCookie = ''
nc_mode=os.environ['NGINX_CONTROLLER_TYPE']
nc_fqdn=os.environ['NGINX_CONTROLLER_FQDN']
nc_user=os.environ['NGINX_CONTROLLER_USERNAME']
nc_pass=os.environ['NGINX_CONTROLLER_PASSWORD']

# Hardware platform types, names and SKU mappings
# https://support.f5.com/csp/article/K4309
# platformcode: platformType|SKU|first letter of the SW reporting SKU
hwPlatforms = {
  "D110": "7250|F5-BIG-7250",
  "D113": "10200|F5-BIG-10200",
  "C113": "4200|F5-BIG-4200",
  "D116": "I15800|F5-BIG-I15800",
  "C124": "I11800|F5-BIG-I11800-DS",
  "C123": "I11800|F5-BIG-I11800",
  "    ": "I10800|F5-BIG-I10800-D",
  "C116": "I10800|F5-BIG-I10800",
  "C126": "I7800|F5-BIG-I7820-DF",
  "    ": "I7800|F5-BIG-I7800-D",
  "C118": "I7800|F5-BIG-I7800",
  "C125": "I5800|F5-BIG-I5820-DF",
  "C119": "I5800|F5-BIG-I5800",
  "C115": "I4800|F5-BIG-I4800",
  "C117": "I2800|F5-BIG-I2800",
  "    ": "C4800|F5-VPR-C4800-DCN",
  "A109": "B2100|F5-VPR-B2100",
  "A113": "B2150|F5-VPR-B2150",
  "A112": "B2250|F5-VPR-B2250",
  "A114": "B4450|F5-VPR-B4450N",
  "F100": "C2400|F5-VPR-C2400-AC",
  "F101": "C2400|F5-VPR-C2400-AC",
  "    ": "C2400|F5-VPR-C2400-ACT",
  "J102": "C4480|F5-VPR-C4480-AC",
  "    ": "C4480|F5-VPR-C4480-DCN",
  "S100": "C4800|F5-VPR-C4800-AC",
  "S101": "C4800|F5-VPR-C4800-AC",
  "Z100": "VE|F5-VE",
  "Z101": "VE-VCMP|F5-VE-VCMP"
}

# SKUs are H-[H|B][platformType]-[swModule]
swModules = {
  "gtm": "DNS",
  "sslo": "SSLO",
  "apm": "APM",
  "cgnat": "CGNAT",
  "ltm": "LTM",
  "avr": "",
  "fps": "",
  "dos": "",
  "lc": "",
  "pem": "PEM",
  "urldb": "",
  "swg": "",
  "asm": "AWF",
  "afm": "AFM",
  "ilx": ""
}

# NGINX dynamic modules
nginxModules = {
  "ngx_http_app_protect_module.so": "nap"
}

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
            r = requests.post(url, data=payload, headers={'Content-Type': 'application/json'}, timeout=10, proxies=proxyDict)
          elif pushmode == 'NGINX_PUSH':
            # Push to pushgateway
            r = requests.post(pushgatewayUrl, data=payload, timeout=10, proxies=proxyDict)
        else:
          if pushmode == 'CUSTOM':
            # Push json to custom URL with basic auth
            r = requests.post(url, auth=(username,password), data=payload, headers={'Content-Type': 'application/json'}, timeout=10, proxies=proxyDict)
          elif pushmode == 'NGINX_PUSH':
            # Push to pushgateway
            r = requests.post(pushgatewayUrl, auth=(username,password), data=payload, timeout=10, proxies=proxyDict)
      except:
        e = sys.exc_info()[0]
        print(datetime.datetime.now(),counter,'Pushing stats to',url,'failed:',e)
      else:
        print(datetime.datetime.now(),counter,'Pushing stats to',url,'returncode',r.status_code)

    except:
      print('Exception caught during push')

    counter = counter + 1

    time.sleep(interval)


# Scheduler for automated email reporting
def scheduledEmail(email_server,email_server_port,email_server_type,email_auth_user,email_auth_pass,email_sender,email_recipient,email_interval):
  while True:
    try:
      if nc_mode == 'NGINX_CONTROLLER':
        payload=ncInstances(mode='JSON')
        jsonPayload=json.loads(payload)
        subscriptionId='['+jsonPayload['subscription']['id']+'] '
        subjectPostfix='NGINX Usage Reporting'
        attachname='nginx_report.json'
      elif nc_mode == 'NGINX_INSTANCE_MANAGER':
        payload=nimInstances(mode='JSON')
        jsonPayload=json.loads(payload)
        subscriptionId='['+jsonPayload['subscription']['id']+'] '
        subjectPostfix='NGINX Usage Reporting'
        attachname='nginx_report.json'
      elif nc_mode == 'BIG_IQ':
        payload=bigIqInventory(mode='JSON')
        subscriptionId=''
        subjectPostfix='BIG-IP Usage Reporting'
        attachname='bigip_report.json'

      dateNow=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      message = EmailMessage()
      message['Subject'] = subscriptionId+'['+dateNow+'] '+subjectPostfix
      message['From'] = email_sender
      message['To'] = email_recipient
      message.set_content('This is the '+subjectPostfix+' for '+dateNow)
      message.add_attachment(payload,filename=attachname)

      if email_server_type == 'ssl':
        context = ssl._create_unverified_context()
        smtpObj = smtplib.SMTP_SSL(email_server,email_server_port,context=context)
      else:
        smtpObj = smtplib.SMTP(email_server,email_server_port)

        if email_server_type == 'starttls':
          smtpObj.starttls()

      if email_auth_user != '' and email_auth_pass != '':
        smtpObj.login(email_auth_user,email_auth_pass)

      smtpObj.sendmail(email_sender, email_recipient, message.as_string())
      print(datetime.datetime.now(),'Reporting email successfully sent to',email_recipient)

    except:
      e = sys.exc_info()[0]
      print(datetime.datetime.now(),'Sending email stats to',url,'failed:',e)

    time.sleep(email_interval)


# Thread for scheduled inventory generation
def scheduledInventory(fqdn,username,password):
  while True:
    # Starts inventory generation task
    # https://clouddocs.f5.com/products/big-iq/mgmt-api/v8.1.0/HowToSamples/bigiq_public_api_wf/t_export_device_inventory.html?highlight=inventory
    print(datetime.datetime.now(),"Requesting BIG-IQ inventory refresh")
    res,body = bigIQcallRESTURI(fqdn = fqdn, username = username, password = password, method = "POST", uri = "/mgmt/cm/device/tasks/device-inventory", body = {'devicesQueryUri': 'https://localhost/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices'} )

    time.sleep(86400)

### NGINX Controller REST API

# NGINX Controller - login
# Returns the session cookie
def nginxControllerLogin(fqdn,username,password):
  data = ('{"credentials":{"type": "BASIC","username": "'+username+'","password": "'+password+'"}}')
  headers = { 'Content-Type': 'application/json' }

  s = Session()
  req = Request('POST',fqdn+"/api/v1/platform/login",data=data,headers=headers)

  p = s.prepare_request(req)
  s.proxies = proxyDict
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
  s.proxies = proxyDict
  p.headers['Cookie']=cookie
  res = s.send(p,verify=False)

  return res.status_code


# Returns NGINX Controller license information
def nginxControllerLicense(fqdn,cookie):
  s = Session()
  req = Request('GET',fqdn+"/api/v1/platform/license")

  p = s.prepare_request(req)
  s.proxies = proxyDict
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
  s.proxies = proxyDict
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
  s.proxies = proxyDict
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


### NGINX Instance Manager REST API

def nginxInstanceManagerRESTCall(method,fqdn,uri):
  s = Session()
  req = Request(method,fqdn+uri)

  p = s.prepare_request(req)
  s.proxies = proxyDict
  res = s.send(p,verify=False)

  if res.status_code == 200:
    data = res.json()
  else:
    data = {}

  return res.status_code,data


### BIG-IQ REST API

# Returns BIG-IP devices managed by BIG-IQ
def bigIQInstances(fqdn,username,password):
  return bigIQcallRESTURI(fqdn = fqdn,username = username,password = password,method = "GET",uri = "/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices",body = "")


# Returns details for a given BIG-IP device
def bigIQInstanceDetails(fqdn,username,password,instanceUUID):
  return bigIQcallRESTURI(fqdn = fqdn,username = username,password = password,method = "GET",uri = "/mgmt/cm/system/machineid-resolver/"+instanceUUID, body = "")


# Returns modules provisioning status details for BIG-IP devices managed by BIG-IQ
def bigIQInstanceProvisioning(fqdn,username,password):
  return bigIQcallRESTURI(fqdn = fqdn,username = username,password = password,method = "GET",uri = "/mgmt/cm/shared/current-config/sys/provision", body ="")


# Returns the most recent inventory for BIG-IP devices managed by BIG-IQ
def bigIQgetInventory(fqdn,username,password):
  # Gets the latest available inventory
  # The "resultsReference" field contains the URL to fetch license/serial number information
  res,body = bigIQcallRESTURI(fqdn = fqdn, username = username,password = password,method = "GET", uri = "/mgmt/cm/device/tasks/device-inventory", body = "" )
  if res != 200:
    return res,body
  else:
    latestUpdate=0
    latestResultsReference=''
    for item in body['items']:
      if item['lastUpdateMicros'] > latestUpdate:
        # "resultsReference": {
        #   "link": "https://localhost/mgmt/cm/device/reports/device-inventory/8982ed9f-1870-4483-96c2-9fb024a2a5b6/results",
        #   "isSubcollection": true
        # }
        latestResultsReference = item['resultsReference']['link'].split('/')[8]
        latestUpdate = item['lastUpdateMicros']

    if latestUpdate == 0:
       return 204,'{}'

    res,body = bigIQcallRESTURI(fqdn = fqdn,username = username,password = password,method = "GET", uri = "/mgmt/cm/device/reports/device-inventory/"+latestResultsReference+"/results", body = "" )

    return res,body


# Invokes the given BIG-IQ REST API method
# The uri must start with '/'
def bigIQcallRESTURI(fqdn,username,password,method,uri,body):
  # Get authorization token
  authRes = requests.request("POST", fqdn+"/mgmt/shared/authn/login", json = {'username': username, 'password': password}, verify=False, proxies=proxyDict)

  if authRes.status_code != 200:
    return authRes.status_code,authRes.json()
  authToken = authRes.json()['token']['token']

  # Invokes the BIG-IQ REST API method
  res = requests.request(method, fqdn+uri, headers = { 'X-F5-Auth-Token': authToken }, json = body, verify=False, proxies=proxyDict)

  data = {}
  if res.status_code == 200 or res.status_code == 202:
    if res.content != '':
      data = res.json()

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

  # Fetches ocations
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
          '"hostname":"' + i['currentStatus']['hostname'] + '",' + \
          '"name":"' + i['metadata']['name'] + '"' + \
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
  status,license = nginxInstanceManagerRESTCall(method='GET',fqdn=nc_fqdn,uri='/api/v0/about/license')

  if status != 200:
    return make_response(jsonify({'error': 'fetching license failed'}), 401)

  # Fetching NIM system information
  status,system = nginxInstanceManagerRESTCall(method='GET',fqdn=nc_fqdn,uri='/api/v0/about/system')
  if status != 200:
    return make_response(jsonify({'error': 'fetching system information failed'}), 401)

  subscriptionId=license['attributes']['subscription']
  instanceType=license['licenses'][0]['product_code']
  instanceVersion=system['version']
  instanceSerial=license['licenses'][0]['serial']
  plusManaged=license['plus_instances_managed']
  totalManaged=license['total_instances_managed']

  # Fetching instances
  status,instances = nginxInstanceManagerRESTCall(method='GET',fqdn=nc_fqdn,uri='/api/v0/instances')

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
      status,configFiles = nginxInstanceManagerRESTCall(method='GET',fqdn=nc_fqdn,uri='/api/v0/instances/'+instanceId+'/config')

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


### BIG-IQ query functions

# Returns NGINX OSS/Plus instances managed by BIG-IQ in JSON format
def bigIqInventory(mode):

  status,details = bigIQInstances(nc_fqdn,nc_user,nc_pass)
  if status != 200:
    return make_response(jsonify(details), status)

  output=''

  if mode == 'JSON':
    output = ''
    firstLoop = True

    # Gets TMOS modules provisioning state for all devices
    rcode,provisioningDetails = bigIQInstanceProvisioning(nc_fqdn,nc_user,nc_pass)
    rcode2,inventoryDetails = bigIQgetInventory(nc_fqdn,nc_user,nc_pass)

    hwSKUGrandTotals={}
    swSKUGrandTotals={}

    for item in details['items']:
      if mode == 'JSON':
        # Gets TMOS registration key and serial number for the current BIG-IP device
        inventoryData = '"inventoryTimestamp":"'+str(inventoryDetails['lastUpdateMicros']//1000)+'",'

        platformType=''

        if rcode2 == 204:
          inventoryData = inventoryData + '"inventoryStatus":"partial",'
        else:
          machineIdFound=False
          for invDevice in inventoryDetails['items']:
            if invDevice['infoState']['machineId'] == item['machineId']:
              machineIdFound=True
              if "errors" in invDevice['infoState']:
                # BIG-IP unreachable, inventory incomplete
                inventoryData = inventoryData + '"inventoryStatus":"partial",'
              else:
                # Get platform name and SKU
                platformCode=invDevice['infoState']['platform']
                platformInsights=''
                if platformCode in hwPlatforms:
                  platformDetails=hwPlatforms[platformCode]
                  platformType=platformDetails.split('|')[0]
                  platformSKU=platformDetails.split('|')[1]

                  if platformSKU in hwSKUGrandTotals:
                    hwSKUGrandTotals[platformSKU] += 1
                  else:
                    hwSKUGrandTotals[platformSKU] = 1

                  platformInsights=',"type":"'+platformType+'","sku":"'+platformSKU+'"'

                #'","licenseEndDateTime":"'+invDevice['infoState']['license']['licenseEndDateTime']+ \
                inventoryData += '"inventoryStatus":"full","platform":{'+ \
                  '"code":"'+platformCode+'"'+platformInsights+'},'+ \
                  '"registrationKey":"'+invDevice['infoState']['license']['registrationKey']+ \
                  '","chassisSerialNumber":"'+invDevice['infoState']['chassisSerialNumber']+'",'

                if 'licenseEndDateTime' in invDevice['infoState']['license']:
                  inventoryData += '"licenseEndDateTime":"'+invDevice['infoState']['license']['licenseEndDateTime']+'",'

          if machineIdFound == False:
            inventoryData = inventoryData + '"inventoryStatus":"partial",'

        # Gets TMOS modules provisioning for the current BIG-IP device
        # https://support.f5.com/csp/article/K4309
        provModules = ''
        pFirstLoop = True
        for prov in provisioningDetails['items']:
          #if prov['deviceReference']['machineId'] == item['uuid']:
          if prov['deviceReference']['machineId'] == item['machineId']:
            if pFirstLoop == True:
              pFirstLoop = False
            else:
              provModules+=','

            # Retrieving relevant SKUs and platform types
            moduleProvisioningLevel=''

            if prov['name'] in swModules:
              moduleName = swModules[prov['name']]
            else:
              moduleName = ''

            if platformType == '' or moduleName == '':
              moduleSKU = ''
            else:
              moduleSKU = "H-"+platformType+"-"+moduleName
              moduleProvisioningLevel=prov['level']

              if moduleProvisioningLevel != 'none':
                if moduleSKU in swSKUGrandTotals:
                  swSKUGrandTotals[moduleSKU] += 1
                else:
                  swSKUGrandTotals[moduleSKU] = 1

            provModules += '{"module":"'+prov['name']+'","level":"'+moduleProvisioningLevel+'","sku":"'+moduleSKU+'"}'

        # Gets TMOS licensed modules for the current BIG-IP device
        #retcode,instanceDetails = bigIQInstanceDetails(nc_fqdn,nc_user,nc_pass,item['uuid'])
        retcode,instanceDetails = bigIQInstanceDetails(nc_fqdn,nc_user,nc_pass,item['machineId'])

        if retcode == 200:
          if instanceDetails != '':
            if firstLoop == True :
              firstLoop = False
            else:
              output+=','

            licensedModules = instanceDetails['properties']['cm:gui:module']

            platformMarketingName=''
            if 'platformMarketingName' in item:
              platformMarketingName=item['platformMarketingName']

            output += '{"hostname":"'+item['hostname']+'","address":"'+item['address']+'","product":"'+item['product']+'","version":"'+item['version']+'","edition":"'+ \
              item['edition']+'","build":"'+item['build']+'","isVirtual":"'+str(item['isVirtual'])+'","isClustered":"'+str(item['isClustered'])+ \
              '","platformMarketingName":"'+platformMarketingName+'","restFrameworkVersion":"'+ \
              item['restFrameworkVersion']+'",'+inventoryData+'"licensedModules":'+str(licensedModules).replace('\'','"')+',"provisionedModules":['+provModules+']}'

    output = '{ "instances": [{ "bigip":"'+str(len(details['items']))+'",'+ \
      '"hwTotals":['+json.dumps(hwSKUGrandTotals)+'],' \
      '"swTotals":['+json.dumps(swSKUGrandTotals)+ \
      ']}], "details": [' + output + ']}'
  elif mode == 'PROMETHEUS' or mode == 'PUSHGATEWAY':
    if mode == 'PROMETHEUS':
      output = '# HELP bigip_online_instances Online BIG-IP instances\n'
      output = output + '# TYPE bigip_online_instances gauge\n'

    output = output + 'bigip_online_instances{instanceType="BIG-IQ",bigiq_url="'+nc_fqdn+'"} '+str(len(details['items']))+'\n'

  return output


# Returns stats in json format
@app.route('/instances', methods=['GET'])
@app.route('/counter/instances', methods=['GET'])
def getInstances():
  if nc_mode == 'NGINX_CONTROLLER':
    return Response(ncInstances(mode='JSON'),mimetype='application/json')
  elif nc_mode == 'NGINX_INSTANCE_MANAGER':
    return Response(nimInstances(mode='JSON'),mimetype='application/json')
  elif nc_mode == 'BIG_IQ':
    return Response(bigIqInventory(mode='JSON'),mimetype='application/json')


# Returns stats in prometheus format
@app.route('/metrics', methods=['GET'])
@app.route('/counter/metrics', methods=['GET'])
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
    # optional HTTP(S) proxy
    if "HTTP_PROXY" in os.environ:
      http_proxy=os.environ['HTTP_PROXY']
      print('Using HTTP Proxy',http_proxy)
    else:
      http_proxy=''
    if "HTTPS_PROXY" in os.environ:
      https_proxy=os.environ['HTTPS_PROXY']
      print('Using HTTPS Proxy',https_proxy)
    else:
      https_proxy=''

    proxyDict = {
      "http": http_proxy,
      "https": https_proxy
    }

    # Push thread
    if nc_mode == 'BIG_IQ':
      print('Running BIG-IQ inventory refresh thread')
      inventoryThread = threading.Thread(target=scheduledInventory,args=(nc_fqdn,nc_user,nc_pass))
      inventoryThread.start()

    if "STATS_PUSH_ENABLE" in os.environ:
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

    if "EMAIL_ENABLED" in os.environ:
      if os.environ['EMAIL_ENABLED'] == 'true':
        email_interval=int(os.environ['EMAIL_INTERVAL'])
        email_sender=os.environ['EMAIL_SENDER']
        email_recipient=os.environ['EMAIL_RECIPIENT']
        email_server=os.environ['EMAIL_SERVER']
        email_server_port=os.environ['EMAIL_SERVER_PORT']
        email_server_type=os.environ['EMAIL_SERVER_TYPE']

        if "EMAIL_AUTH_USER" in os.environ and "EMAIL_AUTH_PASS" in os.environ:
          email_auth_user=os.environ['EMAIL_AUTH_USER']
          email_auth_pass=os.environ['EMAIL_AUTH_PASS']
        else:
          email_auth_user=''
          email_auth_pass=''

        print('Email reporting to',email_recipient,'every',email_interval,'days')
        print('Running push thread')
        emailThread = threading.Thread(target=scheduledEmail,args=(email_server,email_server_port,email_server_type,email_auth_user,email_auth_pass,email_sender,email_recipient,email_interval*60))
        emailThread.start()

    # REST API / prometheus metrics server
    print('Running REST API/Prometheus metrics server')

    nicPort=5000
    nicAddress="0.0.0.0"
    if "NIC_PORT" in os.environ:
      nicPort=os.environ['NIC_PORT']
    if "NIC_ADDRESS" in os.environ:
      nicAddress=os.environ['NIC_ADDRESS']

    app.run(host=nicAddress,port=nicPort)
