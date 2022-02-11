from app.domain.schemas.queries import InstanceQuery, MetricsQuery, ReportingType
from app.conf.agent_settings import *
from app.conf.settings import nc_mode
from app.conf.singleton import Singleton
from app.conf.settings import F5TelemetryConfig
from typing import Callable
import os, sys
import threading
import signal

agents_dir = os.path.abspath("app/core/agents")
sys.path.append(agents_dir)
from bigiq import init as bigiq_init, bigIqInventory, scheduledInventory
from nms import init as nms_init, nmsInstances
from nim import nimInstances
from nc import ncInstances
from app.core.notifiers.push_notifier import scheduledPush
from app.core.notifiers.email_notifier import scheduledEmail


"""
Scheduled push map options:
agent  PE    caller           args
NC
     CUSTOM  ncInstances       fqdn, ncuser,ncpass, json, proxy
     PUSH    ncInstances       fqdn, ncuser,ncpass, push, proxy
NIM
     CUSTOM  nimInstances      fqdn, json, proxy
     PUSH    nimInstances      fqdn, push, proxy
NMS
     CUSTOM  nAttribumsInstances      json
     PUSH    nmsInstances      push
BIGIQ
     CUSTOM  bigiqInventory    json
     PUSH    bigiqInventory    push

req args
     (u or p )        PE       args
       NULL          CUSTOM    url, data=json, headers, to, proxy
       NULL          PUSH      url, data=payl, to, proxy

   non-NULL          CUSTOM    url, data=json, auth=(u,p), headers, to, proxy
   non-NULL          PUSH      url, data=payl, auth=(u,p), to, proxy
"""

class Job(threading.Thread):
    def __init__(self, target, args):
        args = (self,) +  args
        super(Job, self).__init__(target = target, args = args)
        self.shutdown_flag = threading.Event()

    def start(self):
        super(Job, self).start()

    def ok_to_run(self):
        return not self.shutdown_flag.is_set()

    def shutdown(self):
        self.shutdown_flag.set()

@Singleton
class Agent:
    def __init__(self):

        self.agent: agent = agent()
        self.app_settings = F5TelemetryConfig.get_settings()

        # Register with signals
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGUSR1, self.shutdown)

        # Set the agent mode first
        self.agent.agent_mode    = self.app_settings.app_nc_config.nc_mode


        # CVE Tracking
        self.agent.nist_apikey = os.getenv('NIST_API_KEY')

        if self.agent.nist_apikey:
            print("CVE Tracking enabled using key", self.agent.nist_apikey)
        else:
            print("Basic CVE Tracking - for full tracking get a NIST API key at https://nvd.nist.gov/developers/request-an-api-key")

    def initialize_agent_module(self):
        # Proxy settings

        self.agent.agent_proxy = {
                'http': os.getenv('HTTP_PROXY'),
                'https': os.getenv('HTTPS_PROXY'),
        }


        # Set the push notify configuration
        self.agent.agent_push_ctx = self.get_push_mode_config()

        # Set the email notify configuration
        self.agent.agent_email_ctx = self.get_email_mode_config()

        # Set inventory thread context
        self.agent.agent_inventory_ctx = self.get_inventory_context()

        # Set agent_proc_callables
        mode = self.agent.agent_mode
        self.agent_exec_ctx : agent_exec_ctx = agent_exec_ctx()
        self.agent_exec_ctx.fqdn = self.agent.init_params['fqdn']
        self.agent_exec_ctx.username = self.agent.init_params['username']
        self.agent_exec_ctx.password = self.agent.init_params['password']
        self.agent_exec_ctx.proxy = self.agent.init_params['proxy']
        if mode == nc_mode.NGINX_CONTROLLER.value:
            # Callable and params
            self.agent_exec_ctx.agent_exec = ncInstances


        elif mode == nc_mode.NGINX_INSTANCE_MANAGER.value:
            self.agent_exec_ctx.agent_exec = nimInstances

        elif mode == nc_mode.NGINX_MANAGEMENT_SYSTEM.value:
            self.agent_exec_ctx.agent_exec = nmsInstances
        elif mode == nc_mode.BIG_IQ.value:
            self.agent_exec_ctx.agent_exec = bigIqInventory

        if self.is_stats_push_mode():
            self.agent_exec_ctx.mode = 'PUSHGATEWAY'
        else:
            self.agent_exec_ctx.mode = 'JSON'



    def get_inventory_context(self):
        if self.agent.agent_mode == nc_mode.BIG_IQ.value:
            self.agent_inventory_ctx = inventory_context()
            self.agent_inventory_ctx.notify_enabled = True
            self.agent_inventory_ctx.notify_interval = 0

        self.agent.init_params =  {
           'fqdn': self.app_settings.app_nc_config.nc_fqdn,
           'username': self.app_settings.app_nc_config.nc_username,
           'password': self.app_settings.app_nc_config.nc_password,
           'nistApiKey': self.agent.nist_apikey,
           'proxy': self.agent.agent_proxy
        }
        if self.agent.agent_mode == nc_mode.BIG_IQ.value:
             self.agent.init_call = bigiq_init
        if self.agent.agent_mode == nc_mode.NGINX_MANAGEMENT_SYSTEM.value:
             self.agent.init_call = nms_init

    def get_push_mode_config(self):
        push_notify_ctx: push_notify_context = push_notify_context()
        push_notify_ctx.push_thread_ctx = common_notify_context()
        push_notify_ctx.push_thread_ctx.notify_enabled = os.getenv('STATS_PUSH_ENABLE')
        push_notify_ctx.push_thread_ctx.notify_interval = int(os.getenv('STATS_PUSH_INTERVAL'))
        push_notify_ctx.push_notify_mode = os.getenv('STATS_PUSH_MODE')
        if push_notify_ctx.push_notify_mode is None:
            push_notify_ctx.push_notify_mode = os.getenv('CUSTOM_PUSH_MODE')
        push_notify_ctx.push_url = os.getenv('STATS_PUSH_URL')
        push_notify_ctx.push_username = os.getenv('STATS_PUSH_USERNAME')
        push_notify_ctx.push_password = os.getenv('STATS_PUSH_PASSWORD')

        return push_notify_ctx


    def get_email_mode_config(self):
        email_notify_ctx: email_notify_context = email_notify_context()
        email_notify_ctx.email_thread_ctx = common_notify_context()
        email_notify_ctx.email_thread_ctx.notify_enabled = os.getenv('EMAIL_ENABLED')
        email_notify_ctx.email_thread_ctx.notify_interval = int(os.getenv('EMAIL_INTERVAL'))
        email_notify_ctx.email_sender = os.getenv('EMAIL_SENDER')
        email_notify_ctx.email_recipient = os.getenv('EMAIL_RECIPIENT')
        email_notify_ctx.email_server = os.getenv('EMAIL_SERVER')
        email_notify_ctx.email_server_port = os.getenv('EMAIL_SERVER_PORT')
        email_notify_ctx.email_server_type = os.getenv('EMAIL_SERVER_TYPE')
        email_notify_ctx.email_auth_user = os.getenv('EMAIL_AUTH_USER')
        email_notify_ctx.email_auth_pass = os.getenv('EMAIL_AUTH_PASS')

        return email_notify_ctx

    def register_proc_clients_of_agents(self):
        # Register proc calls for all contexts
        pass

    def launch_agent(self):

        # Start the init thread

        if self.agent.init_call:
             param = self.agent.init_params
             self.agent.init_call(
                        fqdn = param['fqdn'],
                        username = param['username'],
                        password = param['password'],
                        nistApiKey = param['nistApiKey'],
                        proxy    = param['proxy']
             )

        # Start the inventory thread
        if self.agent.agent_mode == nc_mode.BIG_IQ.value:
            print("Running BIG-IQ inventory refresh thread")
            target = scheduledInventory
            agent_thread = Job(target = target, args = None)
            self.agent_threads.append(agent_thread)
            agent_thread.start()

        # Start the push-mode thread
        if self.is_push_notify_enabled():
            ctx = self.agent.agent_push_ctx
            assert ctx.push_url != None
            args = ctx.push_url, ctx.push_username, ctx.push_password, \
             ctx.push_thread_ctx.notify_interval,ctx.push_notify_mode
            print("Pushing stats to ", ctx.push_url, " every ",
                ctx.push_thread_ctx.notify_interval, " seconds")
            print("Running push thread")
            agent_thread = Job(target = scheduledPush, args = args)
            self.agent.agent_threads.append(agent_thread)
            agent_thread.start()

        # Start the email-mode thread
        if self.is_email_notify_enabled():
            ctx = self.agent.agent_email_ctx
            args = ctx.email_server, ctx.email_server_port, \
                    ctx.email_server_type, ctx.email_auth_user, \
                    ctx.email_auth_pass, ctx.email_sender, \
                    ctx.email_recipient, \
                    ctx.email_thread_ctx.notify_interval * 60
            print("Email reporting to ", ctx.email_recipient, " every ",
                ctx.email_thread_ctx.notify_interval, " days")
            print("Running push thread")
            agent_thread = Job(target = scheduledEmail, args = args)
            self.agent.agent_threads.append(agent_thread)
            agent_thread.start()

    def shutdown(self, signum, frame):
        print(f"shutting down normally on receiving signal {signum}")
        for agt in self.agent.agent_threads:
            agt.shutdown()
            agt.join()

    def is_push_notify_enabled(self):
        return self.agent.agent_push_ctx.push_thread_ctx.notify_enabled

    def is_email_notify_enabled(self):
        return self.agent.agent_email_ctx.email_thread_ctx.notify_enabled

    def agent_proc(self, pctx: agent_exec_ctx):
        payload = None
        code = 404
        mode = self.agent.agent_mode
        if mode == nc_mode.NGINX_MANAGEMENT_SYSTEM.value or mode == nc_mode.BIGIQ.value:
            payload, code = pctx.agent_exec(mode = pctx.mode)
        elif mode == nc_mode.NGINX_INSTANCE_MANAGER.value:
            payload, code = pctx.agent_exec(fqdn = pctx.fqdn,  mode = pctx.mode,
                proxy = pctx.proxy)
        elif mode == nc_mode.NGINX_CONTROLLER.value:
            payload, code = pctx.agent_exec(fqdn = pctx.fqdn, username = pctx.username,
                password = pctx.password, mode = pctx.mode,
                proxy = pctx.proxy)
        else:
            raise Exception("incorrect mode configuration")

        return payload, code

        
    def is_stats_push_mode(self):
        return self.agent.agent_push_ctx.push_notify_mode == \
                push_notify_type.STATS_PUSH_MODE.value
