from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str
    dataset_url: Optional[str] = None
    inference_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    hmac_secret: Optional[str] = None
    thresholds: Optional[Dict[str, Any]] = None

class ProjectOut(BaseModel):
    id: str
    name: str
    dataset_url: Optional[str] = None
    inference_url: Optional[str] = None
    baseline_run_id: Optional[str] = None

class RunCreate(BaseModel):
    project_id: str
    tag: Optional[str] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0
    dataset_tag: Optional[str] = None  # forwarded to dataset endpoint as ?tag=

class RunOut(BaseModel):
    id: str
    project_id: str
    tag: Optional[str] = None
    status: str

class BaselineSet(BaseModel):
    run_id: str

class MonitorEvent(BaseModel):
    project_id: str
    prompt: str
    output: str
    metadata: Optional[Dict[str, Any]] = None

class ReportOut(BaseModel):
    run_id: str
    project_id: str
    pass_rate: float
    totals: Dict[str, Any]
    by_check: Dict[str, Any]
    failures: List[Dict[str, Any]]
    baseline_diff: Optional[Dict[str, Any]] = None
