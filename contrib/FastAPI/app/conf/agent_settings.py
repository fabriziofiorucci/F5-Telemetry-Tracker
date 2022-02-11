from .apptypes import enumclass
from pydantic import BaseModel, conlist, constr, ValidationError
from typing import Callable
from app.conf.settings import nc_mode

##################
# Agent Settings
##################
class notify_type(enumclass):
    EMAIL_NOTIFY_TYPE   = "email_notify"
    PUSH_NOTIFY_TYPE    = "push_notify"
    INVENTORY_TYPE      = "inventory_type"

class push_notify_type(enumclass):
    STATS_PUSH_MODE    = 'NGINX_PUSH'
    CUSTOM_PUSH_MODE   = 'CUSTOM'

class common_notify_context(BaseModel):
      notify_enabled: bool      = None
      notify_interval: int      = None
      notify_callable: Callable = None
      notify_args:  object      = None

class nc_params(BaseModel):
      fqdn: str         = None
      username: str     = None
      password: str     = None
      mode: str         = None
      proxy: str        = None

class push_notify_context(BaseModel):
      push_thread_ctx: common_notify_context = None
      push_notify_mode: push_notify_type     = None
      push_url: str                          = None
      push_username: str                     = None
      push_password: str                     = None

class email_notify_context(BaseModel):
      email_thread_ctx: common_notify_context = None
      email_sender: str                       = None
      email_recipient: str                    = None
      email_server: str                       = None
      email_server_port: str                  = None
      email_server_type: str                  = None
      email_auth_user: str                    = None
      email_auth_pass: str                    = None

class inventory_context(BaseModel):
    inventory_ctx:   common_notify_context    = None

class agent_exec_ctx(BaseModel):
    agent_exec: Callable                      = None
    fqdn:       str                           = None
    username:   str                           = None
    password:   str                           = None
    mode:       str                           = None
    proxy:      dict                          = None

class agent_proc_ctx_type(enumclass):
    PUSH_SCHED_NOTIFY = 1
    EMAIL_NOTIFY      = 2
    GET_INSTANCE      = 3
    GET_METRICS       = 4
    GET_REPORTING     = 5

class agent(BaseModel):
    agent_mode:          nc_mode              = None
    agent_proxy:         dict                 = None
    nist_apikey:         str                  = None
    agent_push_ctx:      push_notify_context  = None
    agent_email_ctx:     email_notify_context = None
    agent_inventory_ctx: inventory_context    = None
    init_call:           Callable             = None
    init_params:         dict                 = None
    agent_exec_ctx:      agent_exec_ctx       = None
    agent_threads:       list                 = []

########################
# Agent Settings End
########################

