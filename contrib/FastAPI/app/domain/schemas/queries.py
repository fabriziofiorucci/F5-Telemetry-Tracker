from pydantic import BaseModel

class InstanceQuery(BaseModel):
    id: str

class MetricsQuery(BaseModel):
    id: str

class ReportingType(BaseModel):
    report_type: str

