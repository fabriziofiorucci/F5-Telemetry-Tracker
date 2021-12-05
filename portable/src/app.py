#!/usr/bin/python3

import flask
from flask import Flask, jsonify, abort, make_response, request, Response, send_file
import os
import sys
import ssl
import json
import sched, time, datetime
import requests
import time
import threading
import smtplib
import urllib3.exceptions
import base64
from requests import Request, Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from email.message import EmailMessage

# BIG-IQ, NGINX Controller and NGINX Instance Manager modules
import bigiq
import nc
import nim

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

nc_mode = os.environ['NGINX_CONTROLLER_TYPE']
nc_fqdn = os.environ['NGINX_CONTROLLER_FQDN']
nc_user = os.environ['NGINX_CONTROLLER_USERNAME']
nc_pass = os.environ['NGINX_CONTROLLER_PASSWORD']


# Scheduler for automated statistics push / call home
def scheduledPush(url, username, password, interval, pushmode):
    counter = 0

    pushgatewayUrl = url + "/metrics/job/nginx-instance-counter"

    while (counter >= 0):
        try:
            if nc_mode == 'NGINX_CONTROLLER':
                if pushmode == 'CUSTOM':
                    payload = nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='JSON',
                                             proxy=proxyDict)
                elif pushmode == 'NGINX_PUSH':
                    payload = nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='PUSHGATEWAY',
                                             proxy=proxyDict)
            elif nc_mode == 'NGINX_INSTANCE_MANAGER':
                if pushmode == 'CUSTOM':
                    payload = nim.nimInstances(fqdn=nc_fqdn, mode='JSON', proxy=proxyDict)
                elif pushmode == 'NGINX_PUSH':
                    payload = nim.nimInstances(fqdn=nc_fqdn, mode='PUSHGATEWAY', proxy=proxyDict)
            elif nc_mode == 'BIG_IQ':
                if pushmode == 'CUSTOM':
                    payload = bigiq.bigIqInventory(mode='JSON')
                elif pushmode == 'NGINX_PUSH':
                    payload = bigiq.bigIqInventory(mode='PUSHGATEWAY')

            try:
                if username == '' or password == '':
                    if pushmode == 'CUSTOM':
                        # Push json to custom URL
                        r = requests.post(url, data=payload, headers={'Content-Type': 'application/json'}, timeout=10,
                                          proxies=proxyDict)
                    elif pushmode == 'NGINX_PUSH':
                        # Push to pushgateway
                        r = requests.post(pushgatewayUrl, data=payload, timeout=10, proxies=proxyDict)
                else:
                    if pushmode == 'CUSTOM':
                        # Push json to custom URL with basic auth
                        r = requests.post(url, auth=(username, password), data=payload,
                                          headers={'Content-Type': 'application/json'}, timeout=10, proxies=proxyDict)
                    elif pushmode == 'NGINX_PUSH':
                        # Push to pushgateway
                        r = requests.post(pushgatewayUrl, auth=(username, password), data=payload, timeout=10,
                                          proxies=proxyDict)
            except:
                e = sys.exc_info()[0]
                print(datetime.datetime.now(), counter, 'Pushing stats to', url, 'failed:', e)
            else:
                print(datetime.datetime.now(), counter, 'Pushing stats to', url, 'returncode', r.status_code)

        except:
            print('Exception caught during push')

        counter = counter + 1

        time.sleep(interval)


# Scheduler for automated email reporting
def scheduledEmail(email_server, email_server_port, email_server_type, email_auth_user, email_auth_pass, email_sender,
                   email_recipient, email_interval):
    while True:
        try:
            if nc_mode == 'NGINX_CONTROLLER':
                payload = nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='JSON', proxy=proxyDict)
                jsonPayload = json.loads(payload)
                subscriptionId = '[' + jsonPayload['subscription']['id'] + '] '
                subjectPostfix = 'NGINX Usage Reporting'
                attachname = 'nginx_report.json'
            elif nc_mode == 'NGINX_INSTANCE_MANAGER':
                payload = nim.nimInstances(fqdn=nc_fqdn, mode='JSON', proxy=proxyDict)
                jsonPayload = json.loads(payload)
                subscriptionId = '[' + jsonPayload['subscription']['id'] + '] '
                subjectPostfix = 'NGINX Usage Reporting'
                attachname = 'nginx_report.json'
            elif nc_mode == 'BIG_IQ':
                payload = bigiq.bigIqInventory(mode='JSON')
                subscriptionId = ''
                subjectPostfix = 'BIG-IP Usage Reporting'
                attachname = 'bigip_report.json'

            dateNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            message = EmailMessage()
            message['Subject'] = subscriptionId + '[' + dateNow + '] ' + subjectPostfix
            message['From'] = email_sender
            message['To'] = email_recipient
            message.set_content('This is the ' + subjectPostfix + ' for ' + dateNow)
            message.add_attachment(payload, filename=attachname)

            if email_server_type == 'ssl':
                context = ssl._create_unverified_context()
                smtpObj = smtplib.SMTP_SSL(email_server, email_server_port, context=context)
            else:
                smtpObj = smtplib.SMTP(email_server, email_server_port)

                if email_server_type == 'starttls':
                    smtpObj.starttls()

            if email_auth_user != '' and email_auth_pass != '':
                smtpObj.login(email_auth_user, email_auth_pass)

            smtpObj.sendmail(email_sender, email_recipient, message.as_string())
            print(datetime.datetime.now(), 'Reporting email successfully sent to', email_recipient)

        except:
            e = sys.exc_info()[0]
            print(datetime.datetime.now(), 'Sending email stats to',email_recipient,'failed:', e)

        time.sleep(email_interval)


# Returns stats in json format
@app.route('/instances', methods=['GET'])
@app.route('/counter/instances', methods=['GET'])
def getInstances():
    if nc_mode == 'NGINX_CONTROLLER':
        return Response(nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='JSON', proxy=proxyDict),
                        mimetype='application/json')
    elif nc_mode == 'NGINX_INSTANCE_MANAGER':
        return Response(nim.nimInstances(fqdn=nc_fqdn, mode='JSON', proxy=proxyDict), mimetype='application/json')
    elif nc_mode == 'BIG_IQ':
        return Response(bigiq.bigIqInventory(mode='JSON'), mimetype='application/json')


# Returns stats in prometheus format
@app.route('/metrics', methods=['GET'])
@app.route('/counter/metrics', methods=['GET'])
def getMetrics():
    if nc_mode == 'NGINX_CONTROLLER':
        return nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='PROMETHEUS', proxy=proxyDict)
    elif nc_mode == 'NGINX_INSTANCE_MANAGER':
        return nim.nimInstances(fqdn=nc_fqdn, mode='PROMETHEUS', proxy=proxyDict)
    elif nc_mode == 'BIG_IQ':
        return bigiq.bigIqInventory(mode='PROMETHEUS')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':

    if nc_mode != 'NGINX_CONTROLLER' and nc_mode != 'NGINX_INSTANCE_MANAGER' and nc_mode != 'BIG_IQ':
        print('Invalid NGINX_CONTROLLER_TYPE')
    else:
        # optional HTTP(S) proxy
        if "HTTP_PROXY" in os.environ:
            http_proxy = os.environ['HTTP_PROXY']
            print('Using HTTP Proxy', http_proxy)
        else:
            http_proxy = ''
        if "HTTPS_PROXY" in os.environ:
            https_proxy = os.environ['HTTPS_PROXY']
            print('Using HTTPS Proxy', https_proxy)
        else:
            https_proxy = ''

        proxyDict = {
            "http": http_proxy,
            "https": https_proxy
        }

        # CVE tracking
        nist_apikey = ''
        if "NIST_API_KEY" in os.environ:
            nist_apikey = os.environ['NIST_API_KEY']
            print('CVE Tracking enabled using key', nist_apikey)
        else:
            print(
                'Basic CVE Tracking - for full tracking get a NIST API key at https://nvd.nist.gov/developers/request-an-api-key')

        # Push thread
        if nc_mode == 'BIG_IQ':
            bigiq.init(fqdn=nc_fqdn, username=nc_user, password=nc_pass, nistApiKey=nist_apikey, proxy=proxyDict)
            print('Running BIG-IQ inventory refresh thread')
            inventoryThread = threading.Thread(target=bigiq.scheduledInventory)
            inventoryThread.start()

        if "STATS_PUSH_ENABLE" in os.environ:
            if os.environ['STATS_PUSH_ENABLE'] == 'true':
                stats_push_mode = os.environ['STATS_PUSH_MODE']

                if stats_push_mode != 'NGINX_PUSH' and stats_push_mode != 'CUSTOM':
                    print('Invalid STATS_PUSH_MODE')
                else:
                    stats_push_url = os.environ['STATS_PUSH_URL']
                    if "STATS_PUSH_USERNAME" in os.environ:
                        stats_push_username = os.environ['STATS_PUSH_USERNAME']
                    else:
                        stats_push_username = ''

                    if "STATS_PUSH_PASSWORD" in os.environ:
                        stats_push_password = os.environ['STATS_PUSH_PASSWORD']
                    else:
                        stats_push_password = ''

                    stats_push_interval = int(os.environ['STATS_PUSH_INTERVAL'])

                    print('Pushing stats to', stats_push_url, 'every', stats_push_interval, 'seconds')

                    print('Running push thread')
                    pushThread = threading.Thread(target=scheduledPush, args=(
                    stats_push_url, stats_push_username, stats_push_password, stats_push_interval, stats_push_mode))
                    pushThread.start()

        if "EMAIL_ENABLED" in os.environ:
            if os.environ['EMAIL_ENABLED'] == 'true':
                email_interval = int(os.environ['EMAIL_INTERVAL'])
                email_sender = os.environ['EMAIL_SENDER']
                email_recipient = os.environ['EMAIL_RECIPIENT']
                email_server = os.environ['EMAIL_SERVER']
                email_server_port = os.environ['EMAIL_SERVER_PORT']
                email_server_type = os.environ['EMAIL_SERVER_TYPE']

                if "EMAIL_AUTH_USER" in os.environ and "EMAIL_AUTH_PASS" in os.environ:
                    email_auth_user = os.environ['EMAIL_AUTH_USER']
                    email_auth_pass = os.environ['EMAIL_AUTH_PASS']
                else:
                    email_auth_user = ''
                    email_auth_pass = ''

                print('Email reporting to', email_recipient, 'every', email_interval, 'days')
                print('Running push thread')
                emailThread = threading.Thread(target=scheduledEmail, args=(
                email_server, email_server_port, email_server_type, email_auth_user, email_auth_pass, email_sender,
                email_recipient, email_interval * 60))
                emailThread.start()

        # REST API / prometheus metrics server
        print('Running REST API/Prometheus metrics server')

        nicPort = 5000
        nicAddress = "0.0.0.0"
        if "NIC_PORT" in os.environ:
            nicPort = os.environ['NIC_PORT']
        if "NIC_ADDRESS" in os.environ:
            nicAddress = os.environ['NIC_ADDRESS']

        app.run(host=nicAddress, port=nicPort)
