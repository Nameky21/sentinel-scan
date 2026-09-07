from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.db.models import ScanStatus


class ScanCreateRequest(BaseModel):
    target_url: str
    authorization_confirmed: bool
    authorized_by: str | None = None

    @field_validator("target_url")
    @classmethod
    def must_be_http_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("target_url must start with http:// or https://")
        return value.rstrip("/")


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_url: str
    status: ScanStatus
    authorization_confirmed: bool
    authorized_by: str | None
    progress_percent: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


class ScanSummary(ScanResponse):
    findings_by_risk: dict[str, int] = {}
    findings_total: int = 0


class ScanStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ScanStatus
    progress_percent: int
    error_message: str | None


class ScanDeleteAllResponse(BaseModel):
    deleted_count: int
    skipped_count: int
