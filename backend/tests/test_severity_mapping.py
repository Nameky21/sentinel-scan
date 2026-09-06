from app.db.models import Confidence, Risk
from app.services.severity_mapping import parse_confidence, parse_risk


def test_parses_standard_risk_labels():
    assert parse_risk("High") is Risk.HIGH
    assert parse_risk("Medium") is Risk.MEDIUM
    assert parse_risk("Low") is Risk.LOW
    assert parse_risk("Informational") is Risk.INFORMATIONAL


def test_strips_zap_risk_qualifier():
    assert parse_risk("Medium (Suspicious)") is Risk.MEDIUM


def test_unknown_or_missing_risk_falls_back_to_informational():
    assert parse_risk(None) is Risk.INFORMATIONAL
    assert parse_risk("Critical") is Risk.INFORMATIONAL


def test_parses_confidence_including_confirmed():
    assert parse_confidence("Confirmed") is Confidence.CONFIRMED
    assert parse_confidence("high") is Confidence.HIGH
    assert parse_confidence(None) is Confidence.LOW
