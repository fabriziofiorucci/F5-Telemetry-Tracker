from app.conf.agent_settings import agent_exec_ctx
import copy
import time
import json
import requests
import sys
from datetime import datetime


def scheduledPush(parent, url, username, password, interval, pushmode):
    counter = 0
    from app.core.notifiers import get_agent_for_notifiers

    #
    # Ignoring the params received and using the params from agent context
    # as they have been parsed by agent. There is no callback to change the
    # params in between (hopefully not needed now)
    #
    pushgatewayUrl = url + "/metrics/job/f5tt"
    agent = get_agent_for_notifiers()
    while agent == None:
        time.sleep(1)
        agent = get_agent_for_notifiers()
    agent_exec_ctx: agent_exec_ctx = ()
    agent_exec_ctx: agent_exec_ctx = copy.deepcopy(agent.agent_exec_ctx)
    mode = agent.agent.agent_mode

    print("push_mode: entering process loop")

    while counter >= 0:
        try:
            payload, code = agent.agent_proc(agent_exec_ctx)
        except:
            print(datetime.now(), f'push_mode call to {mode} failed:', sys.exc_info())
            print("Exiting...")
            break
        kwargs = {}

        try:
            if agent.is_stats_push_mode():
                args = (pushgatewayUrl)
                kwargs['data'] = payload
            else:
                args = (url)
                kwargs['data'] = json.dumps(payload)
                kwargs['headers'] = {'Content-Type': 'application/json'}
            kwargs['timeout'] = 10
            kwargs['proxies'] = agent_exec_ctx.proxy
            if username is not None and password is not None:
                kwargs['auth'] = (username, password)
            r = requests.post(*args[0], **kwargs)
            
        except:
            e = sys.exc_info()[0]
            print(datetime.now(), counter, 'Pushing stats to', url, 'failed:', e)
        else:
            print(datetime.now(), counter, 'Pushing stats to', url, 'returncode', r.status_code)

        counter = counter + 1

        time.sleep(interval)
        if not parent.ok_to_run():
            print("push_mode: exiting")
            break
