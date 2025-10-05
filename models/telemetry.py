from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class OTLPLog(BaseModel):
    timestamp: datetime
    body: Dict[str, Any]
    attributes: Dict[str, str] = Field(default_factory=dict)
    resource: Dict[str, str] = Field(default_factory=dict)
    service_name: str = "unknown"

class OTLPSpan(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str
    start_time: datetime
    end_time: datetime
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    service_name: str = "unknown"
    status_code: str = "OK"
    status_message: Optional[str] = None

class OTLPMetric(BaseModel):
    name: str
    value: float
    timestamp: datetime
    attributes: Dict[str, str] = Field(default_factory=dict)
    unit: Optional[str] = None

class IncidentPattern(BaseModel):
    id: str
    pattern_type: str  # "log_error", "trace_latency", "metric_anomaly"
    description: str
    symptoms: List[str]
    root_causes: List[str]
    recommendations: List[str]
    severity: str  # "low", "medium", "high", "critical"
    services_affected: List[str]
    created_at: datetime
    updated_at: datetime

class TrainingExample(BaseModel):
    input: str
    output: str
    pattern_type: str
    services: List[str]
    severity: str
    source_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)