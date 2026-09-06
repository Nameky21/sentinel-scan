from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import settings
from app.db.models import Finding, Report, ReportFormat, Risk, Scan
from app.services.remediation_kb import remediation_for
from app.services.severity_mapping import RISK_ORDER

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

RISK_COLORS = {
    Risk.HIGH: "#dc2626",
    Risk.MEDIUM: "#ea580c",
    Risk.LOW: "#ca8a04",
    Risk.INFORMATIONAL: "#64748b",
}


def build_report_context(scan: Scan, findings: list[Finding]) -> dict:
    """Shared context consumed independently by the HTML and PDF renderers."""
    grouped: dict[Risk, list[dict]] = defaultdict(list)
    for finding in findings:
        remediation, is_curated = remediation_for(finding.plugin_id, finding.solution)
        grouped[finding.risk].append(
            {
                "name": finding.name,
                "risk": finding.risk.value,
                "confidence": finding.confidence.value,
                "description": finding.description or "",
                "remediation": remediation,
                "remediation_is_curated": is_curated,
                "affected_url": finding.affected_url or "",
                "param": finding.param or "",
                "evidence": finding.evidence or "",
                "attack": finding.attack or "",
                "cwe_id": finding.cwe_id or "",
                "reference": finding.reference or "",
                "plugin_id": finding.plugin_id or "",
            }
        )

    # Alerts repeat per affected URL; group by name so the report reads as one
    # issue with N affected locations rather than N separate findings.
    sections = []
    for risk in RISK_ORDER:
        items = grouped.get(risk, [])
        if not items:
            continue
        by_name: dict[str, dict] = {}
        for item in items:
            entry = by_name.setdefault(item["name"], {**item, "instances": []})
            if item["affected_url"]:
                entry["instances"].append({"url": item["affected_url"], "param": item["param"]})
        sections.append(
            {
                "risk": risk.value,
                "color": RISK_COLORS[risk],
                "issue_count": len(by_name),
                "instance_count": len(items),
                "issues": sorted(by_name.values(), key=lambda i: i["name"]),
            }
        )

    counts = {risk.value: len(grouped.get(risk, [])) for risk in RISK_ORDER}
    issue_counts = {section["risk"]: section["issue_count"] for section in sections}

    return {
        "scan": {
            "id": scan.id,
            "target_url": scan.target_url,
            "status": scan.status.value,
            "authorized_by": scan.authorized_by or "Not recorded",
            "started_at": _fmt(scan.started_at),
            "completed_at": _fmt(scan.completed_at),
        },
        "generated_at": _fmt(datetime.now(timezone.utc)),
        "sections": sections,
        "instance_counts": counts,
        "issue_counts": issue_counts,
        "total_instances": sum(counts.values()),
        "total_issues": sum(issue_counts.values()),
        "risk_colors": {risk.value: color for risk, color in RISK_COLORS.items()},
    }


def render_html(context: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]))
    return env.get_template("report.html.j2").render(**context)


def render_pdf(context: dict, output_path: Path) -> None:
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        title=f"SentinelScan Report - {context['scan']['target_url']}",
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("t", parent=base["Title"], fontSize=22, spaceAfter=4, alignment=TA_LEFT),
        "subtitle": ParagraphStyle("st", parent=base["Normal"], fontSize=10, textColor=colors.HexColor("#64748b")),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=14, spaceBefore=16, spaceAfter=6),
        "issue": ParagraphStyle("i", parent=base["Heading3"], fontSize=11.5, spaceBefore=10, spaceAfter=2),
        "body": ParagraphStyle("b", parent=base["BodyText"], fontSize=9, leading=12.5),
        "label": ParagraphStyle("l", parent=base["BodyText"], fontSize=8.5, textColor=colors.HexColor("#475569")),
        "mono": ParagraphStyle("m", parent=base["BodyText"], fontSize=8, fontName="Courier", leading=10.5),
    }

    story = [
        Paragraph("SentinelScan Security Report", styles["title"]),
        Paragraph(f"Target: {context['scan']['target_url']}", styles["subtitle"]),
        Paragraph(f"Generated: {context['generated_at']}", styles["subtitle"]),
        Spacer(1, 18),
        Paragraph("Scan details", styles["h2"]),
        _details_table(context),
        Spacer(1, 14),
        Paragraph("Findings summary", styles["h2"]),
        _summary_table(context),
        Paragraph(
            "Counts show distinct issues, with the number of affected locations in brackets.",
            styles["label"],
        ),
    ]

    if context["sections"]:
        story.append(PageBreak())
        for section in context["sections"]:
            story.append(Paragraph(f"{section['risk']} risk findings", styles["h2"]))
            for issue in section["issues"]:
                story.append(KeepTogether(_issue_flowables(issue, section["color"], styles)))
    else:
        story.append(Spacer(1, 12))
        story.append(Paragraph("No findings were reported for this scan.", styles["body"]))

    story.append(Spacer(1, 24))
    story.append(
        Paragraph(
            "Generated by SentinelScan. Scanning was performed against a target the operator confirmed "
            "authorization to test. Automated scanning surfaces candidate issues and does not replace manual "
            "verification — confirm each finding before acting on it.",
            styles["label"],
        )
    )
    doc.build(story)


def _issue_flowables(issue: dict, color: str, styles: dict) -> list:
    flowables = [
        Paragraph(_esc(issue["name"]), ParagraphStyle("x", parent=styles["issue"], textColor=colors.HexColor(color))),
        Paragraph(
            f"Risk: {issue['risk']} &nbsp;|&nbsp; Confidence: {issue['confidence']}"
            + (f" &nbsp;|&nbsp; CWE-{issue['cwe_id']}" if issue["cwe_id"] else "")
            + f" &nbsp;|&nbsp; {len(issue['instances'])} affected location(s)",
            styles["label"],
        ),
        Spacer(1, 5),
    ]
    if issue["description"]:
        flowables.append(Paragraph(_esc(issue["description"]), styles["body"]))
        flowables.append(Spacer(1, 5))

    flowables.append(Paragraph("<b>Remediation</b>", styles["body"]))
    flowables.append(Paragraph(_esc(issue["remediation"]), styles["body"]))

    if issue["instances"]:
        flowables.append(Spacer(1, 5))
        flowables.append(Paragraph("<b>Affected locations</b>", styles["body"]))
        for instance in issue["instances"][:8]:
            suffix = f" (parameter: {instance['param']})" if instance["param"] else ""
            flowables.append(Paragraph(_esc(instance["url"] + suffix), styles["mono"]))
        if len(issue["instances"]) > 8:
            flowables.append(
                Paragraph(f"...and {len(issue['instances']) - 8} more", styles["label"])
            )
    flowables.append(Spacer(1, 10))
    return flowables


def _details_table(context: dict) -> Table:
    scan = context["scan"]
    rows = [
        ["Scan ID", str(scan["id"])],
        ["Target", scan["target_url"]],
        ["Status", scan["status"]],
        ["Authorization", scan["authorized_by"]],
        ["Started", scan["started_at"]],
        ["Completed", scan["completed_at"]],
    ]
    table = Table(rows, colWidths=[1.4 * inch, 5.35 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#e2e8f0")),
            ]
        )
    )
    return table


def _summary_table(context: dict) -> Table:
    rows = [["Severity", "Issues", "Affected locations"]]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]
    for index, risk in enumerate(RISK_ORDER, start=1):
        rows.append(
            [
                risk.value,
                str(context["issue_counts"].get(risk.value, 0)),
                str(context["instance_counts"].get(risk.value, 0)),
            ]
        )
        style.append(("TEXTCOLOR", (0, index), (0, index), colors.HexColor(RISK_COLORS[risk])))
    rows.append(["Total", str(context["total_issues"]), str(context["total_instances"])])
    style.append(("FONTNAME", (0, len(rows) - 1), (-1, len(rows) - 1), "Helvetica-Bold"))

    table = Table(rows, colWidths=[2.75 * inch, 2 * inch, 2 * inch])
    table.setStyle(TableStyle(style))
    return table


def generate_report(scan: Scan, findings: list[Finding], fmt: ReportFormat) -> Report:
    context = build_report_context(scan, findings)
    output_dir = Path(settings.reports_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"scan-{scan.id}-report.{fmt.value}"

    if fmt is ReportFormat.HTML:
        output_path.write_text(render_html(context), encoding="utf-8")
    else:
        render_pdf(context, output_path)

    return Report(scan_id=scan.id, format=fmt, file_path=str(output_path))


def _fmt(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")


def _esc(text: str) -> str:
    """ReportLab Paragraph parses a mini-HTML dialect, so raw markup must be escaped."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
