from pydantic import BaseModel, ConfigDict

from app.db.models import Confidence, Risk


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    plugin_id: str | None
    name: str
    risk: Risk
    confidence: Confidence
    description: str | None
    solution: str | None
    reference: str | None
    affected_url: str | None
    param: str | None
    attack: str | None
    evidence: str | None
    cwe_id: str | None
    wasc_id: str | None
    # Resolved from the remediation knowledge base by the router, not stored.
    remediation: str = ""
    remediation_is_curated: bool = False
