This version is also based on FastAPI and has been revamped with an intent to retain the same behavior as the original code.

Some of the changes/features are:
 - Added poetry package manager and pytests, introduced an agent layer and prometheus middle layer

To run the code:
1. export PYTHONPATH=$TOPDIR
   ln -s app/conf/.env
   poetry shell
   poetry install
   poetry run f5tt   #

    Now the curl commands can be run against the endpoints and notifiers
  
   1.A POST for Requesting a report:
       curl -X POST -H 'content-type: application/json' -d '{"report_type": "report1"}' localhost:6000/api/v1/reporting/report1
   2. Get for instance and metrics
       curl -X GET localhost:6000/api/v1/instances
   3. This endpoint is replied by the prometheus middleware 
       curl -X GET localhost:6000/api/v1/metrics

   Testing:
    poetry run pytests  OR
    pytest 

Set APP_MODE="mock" for mock testing i.e. for testing.

```
Layer:
.
├── README.md
├── app                          # Main application
│   ├── api                      # Apis
│   │   ├── main.py              # Main app level logic
│   │   └── routes               # APIs root
│   │       ├── __init__.py
│   │       ├── instances.py     # Instance EP
│   │       ├── metrics.py       # Metrics EP
│   │       └── reporting.py     # Reporting EP
│   ├── conf                     # App configuration mainly for F5Telemetry
│   │   ├── agent_settings.py    # Agent settings
│   │   ├── apptypes.py          
│   │   ├── .env                 # The environment variables
│   │   ├── settings.py
│   │   └── singleton.py         # Used for F5Telemetry and agent
│   ├── core                     # Core logic
│   │   ├── adapters             # Currently none
│   │   ├── agent.py             # Agent layer for all proxies/agents
│   │   ├── agents               # Currently nc, nim, nis, big_iq
│   │   │   ├── bigiq.py
│   │   │   ├── cveDB.py
│   │   │   ├── nc.py
│   │   │   ├── nim.py
│   │   │   └── nms.py
│   │   ├── middleware           # Currently only Promethueus
│   │   │   └── middlewares.py
│   │   ├── notifiers            # Push and Email notifications
│   │   │   ├── email_notifier.py
│   │   │   └── push_notifier.py
├── poetry.lock 
├── pyproject.toml               # Poetry package manager
├── pytest.ini                   # And for py tests
└── tests
    ├── conftest.py
    ├── env_vars.py
    └── test_conf.py
```
