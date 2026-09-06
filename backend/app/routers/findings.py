from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Finding, Risk, Scan
from app.schemas.finding import FindingResponse
from app.services.severity_mapping import RISK_ORDER

router = APIRouter(prefix="/api/scans", tags=["findings"])


@router.get("/{scan_id}/findings", response_model=list[FindingResponse])
def list_findings(scan_id: int, risk: Risk | None = None, db: Session = Depends(get_db)):
    if db.get(Scan, scan_id) is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    query = select(Finding).where(Finding.scan_id == scan_id)
    if risk is not None:
        query = query.where(Finding.risk == risk)

    findings = db.scalars(query).all()
    return sorted(findings, key=lambda f: (RISK_ORDER.index(f.risk), f.name))
