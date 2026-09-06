from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models import ReportFormat


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    format: ReportFormat
    generated_at: datetime
    download_url: str
