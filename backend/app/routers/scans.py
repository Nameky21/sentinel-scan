from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Finding, Scan, ScanStatus
from app.schemas.scan import ScanCreateRequest, ScanResponse, ScanStatusResponse, ScanSummary
from app.services import scan_orchestrator

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=ScanResponse, status_code=201)
def create_scan(payload: ScanCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not payload.authorization_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Scan authorization must be confirmed: you may only scan targets you own or are explicitly authorized to test.",
        )
    if scan_orchestrator.scan_in_progress():
        raise HTTPException(status_code=409, detail="A scan is already running. Wait for it to finish.")

    scan = Scan(
        target_url=payload.target_url,
        authorization_confirmed=True,
        authorized_by=payload.authorized_by,
        status=ScanStatus.PENDING,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(scan_orchestrator.run_scan, scan.id)
    return scan


@router.get("", response_model=list[ScanSummary])
def list_scans(db: Session = Depends(get_db)):
    scans = db.scalars(select(Scan).order_by(Scan.created_at.desc())).all()
    counts = db.execute(
        select(Finding.scan_id, Finding.risk, func.count(Finding.id)).group_by(Finding.scan_id, Finding.risk)
    ).all()

    by_scan: dict[int, dict[str, int]] = {}
    for scan_id, risk, count in counts:
        by_scan.setdefault(scan_id, {})[risk.value] = count

    summaries = []
    for scan in scans:
        risk_counts = by_scan.get(scan.id, {})
        summary = ScanSummary.model_validate(scan)
        summary.findings_by_risk = risk_counts
        summary.findings_total = sum(risk_counts.values())
        summaries.append(summary)
    return summaries


@router.get("/{scan_id}", response_model=ScanSummary)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = _get_scan_or_404(db, scan_id)
    counts = db.execute(
        select(Finding.risk, func.count(Finding.id)).where(Finding.scan_id == scan_id).group_by(Finding.risk)
    ).all()
    risk_counts = {risk.value: count for risk, count in counts}

    summary = ScanSummary.model_validate(scan)
    summary.findings_by_risk = risk_counts
    summary.findings_total = sum(risk_counts.values())
    return summary


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
def get_scan_status(scan_id: int, db: Session = Depends(get_db)):
    return _get_scan_or_404(db, scan_id)


@router.delete("/{scan_id}", status_code=204)
def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = _get_scan_or_404(db, scan_id)
    db.delete(scan)
    db.commit()


def _get_scan_or_404(db: Session, scan_id: int) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
