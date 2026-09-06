from datetime import datetime, timezone

from app.db.models import Confidence, Finding, Risk, Scan, ScanStatus
from app.services.report_generator import build_report_context, render_html, render_pdf


def make_scan() -> Scan:
    return Scan(
        id=1,
        target_url="http://localhost:3000",
        status=ScanStatus.COMPLETED,
        authorization_confirmed=True,
        authorized_by="local test container",
        progress_percent=100,
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def make_finding(name: str, risk: Risk, url: str, plugin_id: str = "40018") -> Finding:
    return Finding(
        scan_id=1,
        plugin_id=plugin_id,
        name=name,
        risk=risk,
        confidence=Confidence.HIGH,
        description="Example description",
        solution="ZAP solution text",
        affected_url=url,
    )


def test_groups_repeated_alerts_into_one_issue_with_many_locations():
    findings = [
        make_finding("SQL Injection", Risk.HIGH, "http://localhost:3000/a"),
        make_finding("SQL Injection", Risk.HIGH, "http://localhost:3000/b"),
        make_finding("CSP Header Not Set", Risk.MEDIUM, "http://localhost:3000/", plugin_id="10038"),
    ]
    context = build_report_context(make_scan(), findings)

    assert context["total_issues"] == 2
    assert context["total_instances"] == 3
    high = next(section for section in context["sections"] if section["risk"] == "High")
    assert high["issues"][0]["instances"] == [
        {"url": "http://localhost:3000/a", "param": ""},
        {"url": "http://localhost:3000/b", "param": ""},
    ]


def test_sections_are_ordered_by_descending_severity():
    findings = [
        make_finding("Info thing", Risk.INFORMATIONAL, "http://localhost:3000/i", plugin_id="10096"),
        make_finding("SQL Injection", Risk.HIGH, "http://localhost:3000/a"),
    ]
    context = build_report_context(make_scan(), findings)
    assert [section["risk"] for section in context["sections"]] == ["High", "Informational"]


def test_renders_self_contained_html_without_external_assets():
    context = build_report_context(make_scan(), [make_finding("SQL Injection", Risk.HIGH, "http://x/a")])
    html = render_html(context)

    assert "SentinelScan Security Report" in html
    assert "SQL Injection" in html
    assert "<script" not in html
    assert "cdn." not in html


def test_html_escapes_finding_content():
    finding = make_finding("XSS <script>alert(1)</script>", Risk.HIGH, "http://x/a")
    html = render_html(build_report_context(make_scan(), [finding]))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_writes_a_valid_pdf(tmp_path):
    context = build_report_context(make_scan(), [make_finding("SQL Injection", Risk.HIGH, "http://x/a")])
    output = tmp_path / "report.pdf"
    render_pdf(context, output)

    assert output.read_bytes().startswith(b"%PDF-")


def test_renders_when_there_are_no_findings(tmp_path):
    context = build_report_context(make_scan(), [])
    assert context["total_issues"] == 0
    assert "No findings" in render_html(context)
    render_pdf(context, tmp_path / "empty.pdf")
