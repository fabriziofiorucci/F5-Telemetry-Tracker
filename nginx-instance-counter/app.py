#!flask/bin/python
from flask import Flask, jsonify, abort, make_response, request
import os
import sys
import subprocess
import http.client
import ssl
import json

app = Flask(__name__)

conn = ''
sessionCookie = ''
nc_fqdn=os.environ['NGINX_CONTROLLER_FQDN']
nc_user=os.environ['NGINX_CONTROLLER_USERNAME']
nc_pass=os.environ['NGINX_CONTROLLER_PASSWORD']


# Returns the NGINX Controller connection object
def nginxControllerGetConnection(fqdn):
  return http.client.HTTPSConnection(fqdn,context=ssl._create_unverified_context())


# NGINX Controller - login
# Returns the session cookie
def nginxControllerLogin(connection,username,password):
  payload = json.dumps({
    "credentials": {
      "type": "BASIC",
      "username": username,
      "password": password
    }
  })
  headers = { 'Content-Type': 'application/json' }
  connection.request("POST", "/api/v1/platform/login", payload, headers)
  res = connection.getresponse()
  if res.status == 204:
    data = res.read()
    sessionCookie = res.getheader("set-cookie").split(" ", 1)[0].split(";")[0]
  else:
    sessionCookie = ''

  return sessionCookie


# NGINX Controller - logout
# Invalidates the session cookie
def nginxControllerLogout(connection,cookie):
  payload = ''
  headers = { 'Cookie': cookie }
  connection.request("POST", "/api/v1/platform/logout", payload, headers)
  res = connection.getresponse()
  connection.close()

  return ''


# Returns HTTP status (200/401) and NGINX Controller locations dictionary
def nginxControllerLocations(connection,cookie):
  payload = ''
  headers = { 'Cookie': cookie }
  connection.request("GET", "/api/v1/infrastructure/locations", payload, headers)
  res = connection.getresponse()
  if res.status == 200:
    data = res.read()
  else:
    data = '{}'

  return res.status,json.loads(data)


# Returns HTTP status (200/401) and NGINX Plus instances dictionary for the given NGINX Controller location
def nginxControllerInstances(connection,cookie,location):
  payload = ''
  headers = { 'Cookie': cookie }
  connection.request("GET", "/api/v1/infrastructure/locations/"+location+"/instances", payload, headers)
  res = connection.getresponse()
  if res.status == 200:
    data = res.read()
  else:
    data = '{}'

  return res.status,json.loads(data)


# Returns a json for all online/offline instances
@app.route('/instances', methods=['GET'])
def getInstances():
  conn = nginxControllerGetConnection(nc_fqdn)
  sessionCookie = nginxControllerLogin(conn,nc_user,nc_pass)

  # Fetches locations
  status,locations = nginxControllerLocations(conn,sessionCookie)
  if status != 200:
    return make_response(jsonify({'error': 'locations fetch error'}), 404)

  output = '['

  # Iterates locations
  for l in locations['items']:
    if output != '[':
      output+=','

    locName = l['metadata']['name']

    # Iterates and counts online instances
    status,instances = nginxControllerInstances(conn,sessionCookie,locName)
    if status != 200:
      return make_response(jsonify({'error': 'instances fetch error'}), 404)

    online = 0
    offline = 0
    for i in instances['items']:
      if i['currentStatus']['agent']['online'] == True:
        online+=1
      else:
        offline+=1

    output = output + '{"location": "'+locName+'", "online": '+str(online)+', "offline": '+str(offline)+'}'

  nginxControllerLogout(conn,sessionCookie)

  return output+']'


@app.route('/metrics', methods=['GET'])
def getMetrics():
  conn = nginxControllerGetConnection(nc_fqdn)
  sessionCookie = nginxControllerLogin(conn,nc_user,nc_pass)

  # Fetches locations
  status,locations = nginxControllerLocations(conn,sessionCookie)
  if status != 200:
    return status

  output = ''

  # Iterates locations
  for l in locations['items']:

    locName = l['metadata']['name']

    # Iterates and counts online instances
    status,instances = nginxControllerInstances(conn,sessionCookie,locName)
    if status != 200:
      return status

    online = 0
    offline = 0
    for i in instances['items']:
      if i['currentStatus']['agent']['online'] == True:
        online+=1
      else:
        offline+=1

    output = output + '# HELP nginx_online_instances Online NGINX Plus instances\n'
    output = output + '# TYPE nginx_online_instances gauge\n'
    output = output + 'nginx_online_instances{location="'+locName+'"} '+str(online)+'\n'
    output = output + '# HELP nginx_offline_instances Offline NGINX Plus instances\n'
    output = output + '# TYPE nginx_offline_instances gauge\n'
    output = output + 'nginx_offline_instances{location="'+locName+'"} '+str(offline)+'\n'

  nginxControllerLogout(conn,sessionCookie)

  return output


@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':

  app.run(host='0.0.0.0')
