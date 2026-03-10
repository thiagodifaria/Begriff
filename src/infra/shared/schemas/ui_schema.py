from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel


class UiSettingsPayload(BaseModel):
    settings: Dict[str, Any]


class ReportGeneratePayload(BaseModel):
    title: Optional[str] = None
    report_type: str = "analysis_summary"
    analysis_id: Optional[int] = None


class ReportItem(BaseModel):
    id: int
    title: str
    report_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditVerifyPayload(BaseModel):
    hash: str


class ReportScheduleCreatePayload(BaseModel):
    report_type: str
    frequency: str
    recipients: str


class ReportScheduleItem(BaseModel):
    id: int
    report_type: str
    frequency: str
    recipients: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
