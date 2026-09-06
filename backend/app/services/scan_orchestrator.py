import logging
import threading
import time

from app.config import settings
from app.db.database import SessionLocal
from app.db.models import Finding, Scan, ScanStatus, utcnow
from app.services.severity_mapping import parse_confidence, parse_risk
from app.services.zap_client import get_zap

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3

# ZAP alerts accumulate in a single session, so scans run one at a time and each
# starts a fresh ZAP session to keep one scan's findings out of another's results.
_scan_lock = threading.Lock()


def scan_in_progress() -> bool:
    return _scan_lock.locked()


def run_scan(scan_id: int) -> None:
    if not _scan_lock.acquire(blocking=False):
        _fail(scan_id, "Another scan is already running.")
        return
    try:
        _run_scan_locked(scan_id)
    finally:
        _scan_lock.release()


def _run_scan_locked(scan_id: int) -> None:
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return

        target = scan.target_url
        scan.started_at = utcnow()
        db.commit()

        zap = get_zap()
        zap.core.new_session(name=f"sentinelscan-{scan_id}", overwrite=True)
        zap.spider.set_option_max_duration(settings.spider_max_duration_mins)
        zap.ajaxSpider.set_option_browser_id(settings.ajax_spider_browser)
        zap.ajaxSpider.set_option_max_duration(settings.ajax_spider_max_duration_mins)
        zap.ascan.set_option_max_scan_duration_in_mins(settings.ascan_max_duration_mins)

        zap.urlopen(target)
        time.sleep(2)

        _update(db, scan, status=ScanStatus.SPIDERING, progress=0)
        spider_id = zap.spider.scan(target)
        scan.zap_spider_scan_id = str(spider_id)
        db.commit()
        _poll(db, scan, lambda: zap.spider.status(spider_id), start=0, span=20)

        # The traditional spider cannot execute JavaScript, so single-page apps
        # expose almost no attack surface without a browser-driven crawl.
        _run_ajax_spider(db, scan, zap, target)

        _update(db, scan, status=ScanStatus.ACTIVE_SCANNING, progress=45)
        ascan_id = zap.ascan.scan(target)
        scan.zap_ascan_scan_id = str(ascan_id)
        db.commit()
        _poll(db, scan, lambda: zap.ascan.status(ascan_id), start=45, span=54)

        alerts = zap.core.alerts(baseurl=target)
        db.add_all([_to_finding(scan_id, alert) for alert in alerts])

        scan.status = ScanStatus.COMPLETED
        scan.progress_percent = 100
        scan.completed_at = utcnow()
        db.commit()
        logger.info("Scan %s completed with %s findings", scan_id, len(alerts))
    except Exception as exc:
        logger.exception("Scan %s failed", scan_id)
        db.rollback()
        _mark_failed(db, scan_id, str(exc))
    finally:
        db.close()


def _run_ajax_spider(db, scan: Scan, zap, target: str) -> None:
    """Browser-driven crawl. Non-fatal: a missing browser shouldn't abort the scan."""
    # The AJAX spider reports no percentage, only running/stopped, so progress is
    # estimated from elapsed time against its configured ceiling.
    started = time.time()
    budget = settings.ajax_spider_max_duration_mins * 60
    deadline = started + budget + 60
    try:
        zap.ajaxSpider.scan(target)
        while zap.ajaxSpider.status == "running":
            if time.time() > deadline:
                zap.ajaxSpider.stop()
                break
            elapsed_fraction = min(1.0, (time.time() - started) / budget)
            scan.progress_percent = 20 + int(24 * elapsed_fraction)
            db.commit()
            time.sleep(POLL_INTERVAL_SECONDS)
    except Exception:
        logger.warning("AJAX spider unavailable for scan %s; continuing", scan.id, exc_info=True)


def _poll(db, scan: Scan, status_fn, start: int, span: int) -> None:
    while True:
        raw = status_fn()
        try:
            percent = int(raw)
        except (TypeError, ValueError):
            percent = 0
        scan.progress_percent = start + int(span * percent / 100)
        db.commit()
        if percent >= 100:
            return
        time.sleep(POLL_INTERVAL_SECONDS)


def _update(db, scan: Scan, status: ScanStatus, progress: int) -> None:
    scan.status = status
    scan.progress_percent = progress
    db.commit()


def _to_finding(scan_id: int, alert: dict) -> Finding:
    return Finding(
        scan_id=scan_id,
        zap_alert_id=alert.get("id"),
        plugin_id=alert.get("pluginId"),
        name=alert.get("name") or alert.get("alert") or "Unnamed alert",
        risk=parse_risk(alert.get("risk")),
        confidence=parse_confidence(alert.get("confidence")),
        description=alert.get("description"),
        solution=alert.get("solution"),
        reference=alert.get("reference"),
        affected_url=alert.get("url"),
        param=alert.get("param"),
        attack=alert.get("attack"),
        evidence=alert.get("evidence"),
        cwe_id=alert.get("cweid"),
        wasc_id=alert.get("wascid"),
    )


def _mark_failed(db, scan_id: int, message: str) -> None:
    scan = db.get(Scan, scan_id)
    if scan is None:
        return
    scan.status = ScanStatus.FAILED
    scan.error_message = message
    scan.completed_at = utcnow()
    db.commit()


def _fail(scan_id: int, message: str) -> None:
    db = SessionLocal()
    try:
        _mark_failed(db, scan_id, message)
    finally:
        db.close()
