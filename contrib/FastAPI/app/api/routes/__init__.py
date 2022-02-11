from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.api.routes.instances import router as instances_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.reporting import router as reporting_router

router = APIRouter()

# Sub-routes for ...

# Instances
router.include_router(instances_router, prefix="/instances", tags=["instances"])
router.include_router(instances_router, prefix="/counter/instances", tags=["instances"])

# Metrics
router.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
router.include_router(metrics_router, prefix="/counter/metrics", tags=["metrics"])

# Reporting
router.include_router(reporting_router, prefix="/reporting", tags=["reporting"])
router.include_router(reporting_router, prefix="/counter/reporting", tags=["reporting"])


# Root API
@router.get("")
async def root()  -> JSONResponse:
    return JSONResponse(status_code=200,
            content={"message": "Welcome to F5Telemetry"})
