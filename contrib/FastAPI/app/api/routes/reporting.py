from typing import List
from fastapi import APIRouter
from app.core.agent import Agent
from app.domain.schemas.queries import ReportingType
from app.conf.settings import app_settings
from fastapi.responses import JSONResponse
from app.conf.settings import nc_mode
import copy

router = APIRouter()

mock_report = {
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

agent_ctx = None


@router.post("")
async def getReporting(report_type: ReportingType) -> List[dict]:
    global agent_ctx
    if agent_ctx is None:
        agent_ctx = Agent.instance()
    agent_mode = agent_ctx.agent.agent_mode

    if app_settings.app_mode == 'mock':
        return JSONResponse(mock_report)

    elif agent_mode == nc_mode.BIG_IQ.value:
        if reportingType == 'xls':
            instancesJson,code = bigiq.bigIqInventory(mode='JSON')

            if code != 200:
                return JSONResponse(content=json.dumps(instancesJson),status_code=code)

            xlsfile=bigiq.xlsReport(instancesJson)
            headers = {
                'Content-Disposition': 'attachment; filename="bigiq-report.xlsx"'
            }

            return StreamingResponse(xlsfile, headers=headers)

    return JSONResponse(content={"error": "Reporting works only for agent bigiq"},status_code=404)
