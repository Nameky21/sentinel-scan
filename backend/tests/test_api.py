import pytest
from fastapi.testclient import TestClient

from app.db.database import Base, SessionLocal, engine
from app.db.models import Report, ReportFormat, Scan, ScanStatus
from app.main import app


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_requires_authorization_confirmation(client):
    response = client.post(
        "/api/scans",
        json={"target_url": "http://localhost:3000", "authorization_confirmed": False},
    )
    assert response.status_code == 400
    assert "authorization" in response.json()["detail"].lower()


def test_scan_rejects_non_http_target(client):
    response = client.post(
        "/api/scans",
        json={"target_url": "localhost:3000", "authorization_confirmed": True},
    )
    assert response.status_code == 422


def test_unknown_scan_returns_404(client):
    assert client.get("/api/scans/999999").status_code == 404
    assert client.get("/api/scans/999999/findings").status_code == 404
    assert client.delete("/api/scans/999999").status_code == 404


def _clear_scans(db_session):
    db_session.query(Report).delete()
    db_session.query(Scan).delete()
    db_session.commit()


def test_delete_all_scans_when_empty(client, db_session):
    _clear_scans(db_session)
    response = client.request("DELETE", "/api/scans")
    assert response.status_code == 200
    assert response.json() == {"deleted_count": 0, "skipped_count": 0}


def test_delete_completed_scan_removes_row_and_files(client, db_session, tmp_path):
    _clear_scans(db_session)
    report_path = tmp_path / "scan-report.html"
    report_path.write_text("<html></html>")

    scan = Scan(target_url="http://localhost:3000", status=ScanStatus.COMPLETED, authorization_confirmed=True)
    db_session.add(scan)
    db_session.commit()
    db_session.refresh(scan)

    report = Report(scan_id=scan.id, format=ReportFormat.HTML, file_path=str(report_path))
    db_session.add(report)
    db_session.commit()

    response = client.delete(f"/api/scans/{scan.id}")
    assert response.status_code == 204
    assert client.get(f"/api/scans/{scan.id}").status_code == 404
    assert not report_path.exists()


def test_delete_running_scan_returns_409(client, db_session):
    _clear_scans(db_session)
    scan = Scan(target_url="http://localhost:3000", status=ScanStatus.ACTIVE_SCANNING, authorization_confirmed=True)
    db_session.add(scan)
    db_session.commit()
    db_session.refresh(scan)

    response = client.delete(f"/api/scans/{scan.id}")
    assert response.status_code == 409
    assert client.get(f"/api/scans/{scan.id}").status_code == 200


def test_delete_all_scans_skips_running(client, db_session):
    _clear_scans(db_session)
    completed = Scan(target_url="http://localhost:3000", status=ScanStatus.COMPLETED, authorization_confirmed=True)
    failed = Scan(target_url="http://localhost:3000", status=ScanStatus.FAILED, authorization_confirmed=True)
    running = Scan(target_url="http://localhost:3000", status=ScanStatus.SPIDERING, authorization_confirmed=True)
    db_session.add_all([completed, failed, running])
    db_session.commit()
    db_session.refresh(completed)
    db_session.refresh(failed)
    db_session.refresh(running)

    response = client.request("DELETE", "/api/scans")
    assert response.status_code == 200
    assert response.json() == {"deleted_count": 2, "skipped_count": 1}
    assert client.get(f"/api/scans/{completed.id}").status_code == 404
    assert client.get(f"/api/scans/{failed.id}").status_code == 404
    assert client.get(f"/api/scans/{running.id}").status_code == 200
