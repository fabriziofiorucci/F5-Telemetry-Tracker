from typing import List
from fastapi import APIRouter, Response
from app.core.agent import Agent
from app.domain.schemas.queries import MetricsQuery
from app.conf.settings import app_settings
from fastapi.responses import JSONResponse
from app.conf.agent_settings import agent_exec_ctx
import copy

router = APIRouter()

mock_metrics = {
     "subscription": { "id": "NGX-Subscription-]-TRL-XXXXXX",
     "type": "    INSTANCE_MANAGER", "version": "1.0.2",
     "serial": "6232847160738694" },
     "instances": [
         { "    nginx_plus_online": 0, "nginx_oss_online": 1 } ],
     "details": [ { "instance_id": "c613e90d-3051-4090-b9cd-a32cb725b785",
               "uname": "Linux vm-gw 5.7.6 #1 SMP PREEMPT Fri Jun 26 17:39:22 CEST 2020 x86_64 QEMU Virtual CPU version 2.5+ AuthenticAMD GNU/Linux",
               "containerized": False, "type": "oss", "version": "1.20.1",
               "last_seen": "2021-08-31T11:37:04.587986759Z",
               "createtime": "2021-08-18T22:02:49.717530751Z",
               "modules": {},"networkconfig": {
                    "host_ips": [ "192.168.1.5", "192.168.1.27" ] },
                    "hostname": "vm-gw", "CVE": [ {} ] } ]
}

exec_ctx: agent_exec_ctx = None
agent = None

@router.get("")
async def getMetrics() -> List[dict]:
    global exec_ctx, agent

    if app_settings.app_mode == 'mock':
        return JSONResponse(mock_metrics)

    elif exec_ctx is None:
        agent = Agent.instance()
        if exec_ctx is None:
            exec_ctx = agent_exec_ctx()
            exec_ctx = copy.deepcopy(agent.agent_exec_ctx)
    
    reply, code = agent.agent_proc(exec_ctx)

    return Response(str(reply), media_type="text/plain")
