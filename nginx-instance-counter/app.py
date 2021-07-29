#!flask/bin/python
from flask import Flask, jsonify, abort, make_response, request
import os
import sys
import ssl
import json
import sched,time,datetime
import requests
from requests import Request, Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

conn = ''
sessionCookie = ''
nc_mode=os.environ['NGINX_CONTROLLER_TYPE']
nc_fqdn=os.environ['NGINX_CONTROLLER_FQDN']
nc_user=os.environ['NGINX_CONTROLLER_USERNAME']
nc_pass=os.environ['NGINX_CONTROLLER_PASSWORD']


# Scheduler for automated statistics push / call home
def scheduledPush(counter):
  if nc_mode == 'NGINX_CONTROLLER':
    payload=ncInstances(mode='JSON')
  elif nc_mode == 'NGINX_INSTANCE_MANAGER':
    payload=nimInstances(mode='JSON')

  try:
    if stats_push_username == '' or stats_push_password == '':
      r = requests.post(stats_push_url, data=payload, headers={ 'Content-Type': 'application/json'})
    else:
      r = requests.post(stats_push_url, auth=(stats_push_username,stats_push_password), data=payload, headers={ 'Content-Type': 'application/json'})
  except:
    e = sys.exc_info()[0]
    print(datetime.datetime.now(),counter,'Pushing stats to',stats_push_url,'failed:',e)
  else:
    print(datetime.datetime.now(),counter,'Pushing stats to',stats_push_url,'returncode',r.status_code)

  scheduler.enter(stats_push_interval,1,scheduledPush,(counter+1,))
  scheduler.run()


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

  return ''


# Returns HTTP status (200/401) and NGINX Controller locations dictionary
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


# Returns HTTP status (200/401) and NGINX Plus instances dictionary for the given NGINX Controller location
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

# ReturnsNGINX OSS/Plus instances managed by NIM
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


### NGINX Controller query functions

# Returns NGINX Plus instances managed by NGINX Controller in JSON format
def ncInstances(mode):
  status,sessionCookie = nginxControllerLogin(nc_fqdn,nc_user,nc_pass)

  if status != 204:
    return make_response(jsonify({'error': 'authentication failed'}), 401)

  # Fetches locations
  status,locations = nginxControllerLocations(nc_fqdn,sessionCookie)
  if status != 200:
    return make_response(jsonify({'error': 'locations fetch error'}), 404)

  if mode == 'JSON':
    output = '['
  else:
    output = ''

  # Iterates locations
  for l in locations['items']:
    if mode == 'JSON':
      if output != '[':
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
      output = output + '{"location": "'+locName+'", "online": '+str(online)+', "offline": '+str(offline)+'}'
    elif mode == 'PROMETHEUS':
      output = output + '# HELP nginx_online_instances Online NGINX Plus instances\n'
      output = output + '# TYPE nginx_online_instances gauge\n'
      output = output + 'nginx_online_instances{location="'+locName+'"} '+str(online)+'\n'
      output = output + '# HELP nginx_offline_instances Offline NGINX Plus instances\n'
      output = output + '# TYPE nginx_offline_instances gauge\n'
      output = output + 'nginx_offline_instances{location="'+locName+'"} '+str(offline)+'\n'

  nginxControllerLogout(nc_fqdn,sessionCookie)

  if mode == 'JSON':
    output = output + ']'

  return output


### NGINX Instance Manager query functions

# Returns NGINX OSS/Plus instances managed by NIM in JSON format
def nimInstances(mode):
  # Fetches instances
  status,instances = nginxInstanceManagerInstances(nc_fqdn)

  if status != 200:
    return make_response(jsonify({'error': 'instances fetch error'}), 404)

  if mode == 'JSON':
    output = '[ {"location": "", "online": '+str(instances['listinfo']['total'])+', "offline": 0} ]'
  elif mode == 'PROMETHEUS':
    output = '# HELP nginx_online_instances Online NGINX OSS/Plus instances\n'
    output = output + '# TYPE nginx_online_instances gauge\n'
    output = output + 'nginx_online_instances{location=""} '+str(instances['listinfo']['total'])+'\n'
    output = output + '# HELP nginx_offline_instances Offline NGINX OSS/Plus instances\n'
    output = output + '# TYPE nginx_offline_instances gauge\n'
    output = output + 'nginx_offline_instances{location=""} 0\n'

  return output



# Returns stats in json format
@app.route('/instances', methods=['GET'])
def getInstances():
  if nc_mode == 'NGINX_CONTROLLER':
    return ncInstances(mode='JSON')
  elif nc_mode == 'NGINX_INSTANCE_MANAGER':
    return nimInstances(mode='JSON')


# Returns stats in prometheus format
@app.route('/metrics', methods=['GET'])
def getMetrics():
  if nc_mode == 'NGINX_CONTROLLER':
    return ncInstances(mode='PROMETHEUS')
  elif nc_mode == 'NGINX_INSTANCE_MANAGER':
    return nimInstances(mode='PROMETHEUS')


@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':

  if nc_mode != 'NGINX_CONTROLLER' and nc_mode != 'NGINX_INSTANCE_MANAGER':
    print('Invalid NGINX_CONTROLLER_TYPE')
  else:
    if os.environ['STATS_PUSH_ENABLE'] == 'true':
      # Push mode
      print('Running in push mode')

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

      scheduler = sched.scheduler(time.time,time.sleep)
      scheduler.enter(stats_push_interval,1,scheduledPush,(0,))
      scheduler.run()
    else:
      # REST API mode
      print('Running in REST API mode')
      app.run(host='0.0.0.0')
