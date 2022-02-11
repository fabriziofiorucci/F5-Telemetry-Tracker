from app.conf.agent_settings import agent_exec_ctx
from app.conf.settings import nc_mode
import copy
import json
import sys
import time
from datetime import datetime
from email.message import EmailMessage
import smtplib
import ssl


def scheduledEmail(parent, email_server, email_server_port, email_server_type,
    email_auth_user, email_auth_pass, email_sender, email_recipient,
    email_interval):
    from app.core.notifiers import get_agent_for_notifiers
    counter = 0

    agent = get_agent_for_notifiers()
    while agent == None:
        time.sleep(1)
        agent = get_agent_for_notifiers()
    agent_exec_ctx: agent_exec_ctx = ()
    agent_exec_ctx: agent_exec_ctx = copy.deepcopy(agent.agent_exec_ctx)
    mode = agent.agent.agent_mode

    print("email_mode: entering process loop")

    while counter >= 0:
        try:
            try:
                payload, code = agent.agent_proc(agent_exec_ctx)
            except:
                print(datetime.now(), f'email_mode call to {mode} failed:', sys.exc_info())
                print("Exiting...")
                break

            if mode == nc_mode.NGINX_CONTROLLER.value:
                subscriptionId = '[' + payload['subscription']['id'] + '] '
                subjectPostfix = 'NGINX Usage Reporting'
                attachname = 'nginx_report.json'

            elif mode == nc_mode.NGINX_INSTANCE_MANAGER.value:
                subscriptionId = '[' + payload['subscription']['id'] + '] '
                subjectPostfix = 'NGINX Usage Reporting'
                attachname = 'nginx_report.json'

            elif mode == nc_mode.NGINX_MANAGEMENT_SYSTEM.value:
                subscriptionId = '[' + payload['subscription']['id'] + '] '
                subjectPostfix = 'NGINX Usage Reporting'
                attachname = 'nginx_report.json'

            elif mode == nc_mode.BIG_IQ.value:
                payload,code = bigiq.bigIqInventory(mode='JSON')
                subscriptionId = ''
                subjectPostfix = 'BIG-IP Usage Reporting'
                attachname = 'bigip_report.json'

            dateNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            message = EmailMessage()
            message['Subject'] = subscriptionId + '[' + dateNow + '] ' + subjectPostfix
            message['From'] = email_sender
            message['To'] = email_recipient
            message.set_content('This is the ' + subjectPostfix + ' for ' + dateNow)

            attachment = json.dumps(payload)
            bs = attachment.encode('utf-8')
            message.add_attachment(bs,maintype='application',subtype='json',filename=attachname)

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
            print(datetime.now(), 'Reporting email successfully sent to', email_recipient)

        except:
            print(datetime.now(), 'Sending email stats to',email_recipient,'failed:', sys.exc_info())

        time.sleep(email_interval)
        if not parent.ok_to_run():
            print("email_mode: exiting")
            break
