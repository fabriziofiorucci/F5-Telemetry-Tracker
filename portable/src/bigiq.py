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

this = sys.modules[__name__]

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Hardware platform types, names and SKU mappings
# https://support.f5.com/csp/article/K4309
hwPlatforms = {
  "D110": "7250|F5-BIG-7250",
  "D113": "10200|F5-BIG-10200",
  "C113": "4200|F5-BIG-4200",
  "D116": "I15800|F5-BIG-I15800",
  "C124": "I11800|F5-BIG-I11800-DS",
  "C123": "I11800|F5-BIG-I11800",
  "    ": "I10800|F5-BIG-I10800-D",
  "C116": "I10800|F5-BIG-I10800",
  "C126": "I7820-DF|F5-BIG-I7820-DF",
  "    ": "I7800|F5-BIG-I7800-D",
  "C118": "I7800|F5-BIG-I7800",
  "C125": "I5820-DF|F5-BIG-I5820-DF",
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

# TMOS modules SKU
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

this.bigiq_fqdn=''
this.bigiq_username=''
this.bigiq_password=''
this.bigiq_proxy={}

# Module initialization
def init(fqdn,username,password,proxy,nistApiKey):
  this.bigiq_fqdn=fqdn
  this.bigiq_username=username
  this.bigiq_password=password
  this.bigiq_proxy=proxy

  cveDB.init(nistApiKey=nistApiKey,proxy=proxy)


# Thread for scheduled inventory generation
def scheduledInventory():
  while True:
    # Starts inventory generation task
    # https://clouddocs.f5.com/products/big-iq/mgmt-api/v8.1.0/HowToSamples/bigiq_public_api_wf/t_export_device_inventory.html?highlight=inventory
    print(datetime.datetime.now(),"Requesting BIG-IQ inventory refresh")
    res,body = bigIQcallRESTURI(method = "POST", uri = "/mgmt/cm/device/tasks/device-inventory", body = {'devicesQueryUri': 'https://localhost/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices'} )

    time.sleep(86400)


### BIG-IQ REST API

# Returns BIG-IP devices managed by BIG-IQ
def bigIQInstances():
  return bigIQcallRESTURI(method = "GET",uri = "/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices",body = "")


# Returns details for a given BIG-IP device
def bigIQInstanceDetails(instanceUUID):
  return bigIQcallRESTURI(method = "GET",uri = "/mgmt/cm/system/machineid-resolver/"+instanceUUID, body = "")


# Returns modules provisioning status details for BIG-IP devices managed by BIG-IQ
def bigIQInstanceProvisioning():
  return bigIQcallRESTURI(method = "GET",uri = "/mgmt/cm/shared/current-config/sys/provision", body ="")


# Returns the most recent inventory for BIG-IP devices managed by BIG-IQ
def bigIQgetInventory():
  # Gets the latest available inventory
  # The "resultsReference" field contains the URL to fetch license/serial number information
  res,body = bigIQcallRESTURI(method = "GET", uri = "/mgmt/cm/device/tasks/device-inventory", body = "" )
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

    res,body = bigIQcallRESTURI(method = "GET", uri = "/mgmt/cm/device/reports/device-inventory/"+latestResultsReference+"/results", body = "" )

    return res,body


# Invokes the given BIG-IQ REST API method
# The uri must start with '/'
def bigIQcallRESTURI(method,uri,body):
  # Get authorization token
  authRes = requests.request("POST", this.bigiq_fqdn+"/mgmt/shared/authn/login", json = {'username': this.bigiq_username, 'password': this.bigiq_password}, verify=False, proxies=this.bigiq_proxy)

  if authRes.status_code != 200:
    return authRes.status_code,authRes.json()
  authToken = authRes.json()['token']['token']

  # Invokes the BIG-IQ REST API method
  res = requests.request(method, this.bigiq_fqdn+uri, headers = { 'X-F5-Auth-Token': authToken }, json = body, verify=False, proxies=this.bigiq_proxy)

  data = {}
  if res.status_code == 200 or res.status_code == 202:
    if res.content != '':
      data = res.json()

  return res.status_code,data


### BIG-IQ query functions

# Returns TMOS instances managed by BIG-IQ in JSON format
def bigIqInventory(mode):

  status,details = bigIQInstances()
  if status != 200:
    return make_response(jsonify(details), status)

  output=''

  if mode == 'JSON':
    output = ''
    firstLoop = True

    # Gets TMOS modules provisioning state for all devices
    rcode,provisioningDetails = bigIQInstanceProvisioning()
    rcode2,inventoryDetails = bigIQgetInventory()

    hwSKUGrandTotals={}
    swSKUGrandTotals={}
    wholeInventory=[]

    for item in details['items']:
      if mode == 'JSON':
        # Gets TMOS registration key and serial number for the current BIG-IP device
        inventoryData = {}
        inventoryData['inventoryTimestamp'] = inventoryDetails['lastUpdateMicros']//1000

        platformType=''

        if rcode2 == 204:
          inventoryData['inventoryStatus']="partial"
        else:
          machineIdFound=False
          for invDevice in inventoryDetails['items']:
            if invDevice['infoState']['machineId'] == item['machineId']:
              machineIdFound=True
              if "errors" in invDevice['infoState']:
                # BIG-IP unreachable, inventory incomplete
                inventoryData['inventoryStatus']="partial"
              else:
                # Get platform name and SKU
                platformCode=invDevice['infoState']['platform']
                platformInsights={}
                if platformCode in hwPlatforms:
                  platformDetails=hwPlatforms[platformCode]
                  platformType=platformDetails.split('|')[0]
                  platformSKU=platformDetails.split('|')[1]

                  if platformSKU in hwSKUGrandTotals:
                    hwSKUGrandTotals[platformSKU] += 1
                  else:
                    hwSKUGrandTotals[platformSKU] = 1

                  platformInsights['type']=platformType
                  platformInsights['sku']=platformSKU

                platformInsights['code']=platformCode

                inventoryData['inventoryStatus'] = "full"
                inventoryData['registrationKey'] = invDevice['infoState']['license']['registrationKey']
                inventoryData['chassisSerialNumber'] = invDevice['infoState']['chassisSerialNumber'].strip()
                inventoryData['platform'] = platformInsights

                if 'licenseEndDateTime' in invDevice['infoState']['license']:
                  inventoryData['licenseEndDateTime']=invDevice['infoState']['license']['licenseEndDateTime']

          if machineIdFound == False:
            inventoryData['inventoryStatus']="partial"

        # Gets TMOS modules provisioning for the current BIG-IP device
        # https://support.f5.com/csp/article/K4309
        provModules = {}
        provModules['provisionedModules']=[]

        foundCVEs={}

        for prov in provisioningDetails['items']:
          if prov['deviceReference']['machineId'] == item['machineId']:

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
                # CVE tracking
                allCVE=cveDB.getF5(product=prov['name'],version=item['version'])
                foundCVEs.update(allCVE)

                if moduleSKU in swSKUGrandTotals:
                  swSKUGrandTotals[moduleSKU] += 1
                else:
                  swSKUGrandTotals[moduleSKU] = 1

            thisModule = {}
            thisModule['module']=prov['name']
            thisModule['level']=moduleProvisioningLevel
            thisModule['sku']=moduleSKU

            provModules['provisionedModules'].append(thisModule)

        # Gets TMOS licensed modules for the current BIG-IP device
        retcode,instanceDetails = bigIQInstanceDetails(item['machineId'])

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

            inventoryData['hostname']=item['hostname']
            inventoryData['address']=item['address']
            inventoryData['product']=item['product']
            inventoryData['version']=item['version']
            inventoryData['edition']=item['edition']
            inventoryData['build']=item['build']
            inventoryData['isVirtual']=item['isVirtual']
            inventoryData['isClustered']=item['isClustered']
            inventoryData['platformMarketingName']=platformMarketingName
            inventoryData['restFrameworkVersion']=item['restFrameworkVersion']
            inventoryData['licensedModules']=licensedModules
            inventoryData['provisionedModules']=provModules['provisionedModules']
            inventoryData['CVE']=[]
            inventoryData['CVE'].append(foundCVEs)

            wholeInventory.append(inventoryData)

    instancesDict={}
    instancesDict['bigip']=len(details['items'])
    instancesDict['hwTotals'] = []
    instancesDict['hwTotals'].append(hwSKUGrandTotals)
    instancesDict['swTotals'] = []
    instancesDict['swTotals'].append(swSKUGrandTotals)

    output = {}
    output['instances'] = []
    output['instances'].append(instancesDict)
    output['details'] = wholeInventory
    output['telemetry'] = []
    output['telemetry'] = bigIqTelemetry(mode)

    output=str(json.dumps(output))

  elif mode == 'PROMETHEUS' or mode == 'PUSHGATEWAY':
    if mode == 'PROMETHEUS':
      output = '# HELP bigip_online_instances Online BIG-IP instances\n'
      output = output + '# TYPE bigip_online_instances gauge\n'

    output = output + 'bigip_online_instances{instanceType="BIG-IQ",bigiq_url="'+bigiq_fqdn+'"} '+str(len(details['items']))+'\n'

  return output


# Builds BIG-IQ telemetry request body
def _getTelemetryRequestBody(module,metricSet,timeRange):

  tr = {}
  tr['from'] = timeRange
  tr['to'] = "now"

  aggregations = {}
  aggregations[metricSet+'$avg-value-per-event'] = {}
  aggregations[metricSet+'$avg-value-per-event']['metricSet'] = metricSet
  aggregations[metricSet+'$avg-value-per-event']['metric'] = "avg-value-per-event"

  body = {}
  body['kind'] = "ap:query:stats:byEntities"
  body['module'] = module
  body['dimension'] = "hostname"
  body['timeRange'] = tr
  body['aggregations'] = aggregations

  return body

# Returns TMOS instances telemetry
def bigIqTelemetry(mode):
  telemetryURI = "/mgmt/ap/query/v1/tenants/default/products/device/metric-query"

  allStats = [
    { "module":"bigip-cpu","metricSet":"cpu-usage","timeRange":"-1H" },
    { "module":"bigip-cpu","metricSet":"cpu-usage","timeRange":"-1W" },
    { "module":"bigip-cpu","metricSet":"cpu-usage","timeRange":"-1M" },
    { "module":"bigip-memory","metricSet":"free-ram","timeRange":"-1H" },
    { "module":"bigip-memory","metricSet":"free-ram","timeRange":"-1W" },
    { "module":"bigip-memory","metricSet":"free-ram","timeRange":"-1M" }
  ]

  telemetryBody={}

  if mode == 'JSON':
    for stat in allStats:
      res,body = bigIQcallRESTURI(method = "POST", uri = telemetryURI, body = _getTelemetryRequestBody(module=stat['module'],metricSet=stat['metricSet'],timeRange=stat['timeRange']) )

      if res == 200:
        for r in body['result']['result']: 
          telHostname = r['hostname']
          telTimeRange = stat['timeRange']
          telVarName = stat['metricSet']
          telVarValue = r[stat['metricSet']+'$avg-value-per-event']

          if telHostname not in telemetryBody:
            telemetryBody[telHostname] = {}

          if telVarName not in telemetryBody[telHostname]:
            telemetryBody[telHostname][telVarName] = {}

          telemetryBody[telHostname][telVarName][telTimeRange] = telVarValue

    return json.dumps(telemetryBody)
  elif mode == 'PROMETHEUS' or mode == 'PUSHGATEWAY':
    print("PROMETHEUS/PUSHGATEWAY")
  else:
    return json.dumps(telemetryBody)
