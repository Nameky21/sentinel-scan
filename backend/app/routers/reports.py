from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Finding, Report, ReportFormat, Scan
from app.schemas.report import ReportResponse
from app.services import report_generator

router = APIRouter(prefix="/api/scans", tags=["reports"])

MEDIA_TYPES = {ReportFormat.HTML: "text/html", ReportFormat.PDF: "application/pdf"}


@router.post("/{scan_id}/report", response_model=ReportResponse)
def create_report(scan_id: int, format: ReportFormat = ReportFormat.HTML, db: Session = Depends(get_db)):
    scan = _get_scan_or_404(db, scan_id)
    findings = db.scalars(select(Finding).where(Finding.scan_id == scan_id)).all()

    existing = db.scalars(
        select(Report).where(Report.scan_id == scan_id, Report.format == format)
    ).all()
    for report in existing:
        db.delete(report)

    report = report_generator.generate_report(scan, list(findings), format)
    db.add(report)
    db.commit()
    db.refresh(report)

    return _to_response(report)


@router.get("/{scan_id}/report/{format}")
def download_report(scan_id: int, format: ReportFormat, db: Session = Depends(get_db)):
    report = db.scalars(
        select(Report).where(Report.scan_id == scan_id, Report.format == format)
    ).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not generated yet")

    path = Path(report.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file is missing; regenerate it")

    # Inline so the UI's "open report" shows it in the browser; the browser's own
    # save action still uses the filename.
    return FileResponse(
        path,
        media_type=MEDIA_TYPES[format],
        filename=path.name,
        content_disposition_type="inline",
    )


def _to_response(report: Report) -> ReportResponse:
    return ReportResponse(
        id=report.id,
        scan_id=report.scan_id,
        format=report.format,
        generated_at=report.generated_at,
        download_url=f"/api/scans/{report.scan_id}/report/{report.format.value}",
    )


def _get_scan_or_404(db: Session, scan_id: int) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
