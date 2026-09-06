from app.db.models import Confidence, Risk

RISK_ORDER = [Risk.HIGH, Risk.MEDIUM, Risk.LOW, Risk.INFORMATIONAL]

_RISK_LOOKUP = {
    "high": Risk.HIGH,
    "medium": Risk.MEDIUM,
    "low": Risk.LOW,
    "informational": Risk.INFORMATIONAL,
    "info": Risk.INFORMATIONAL,
}

_CONFIDENCE_LOOKUP = {
    "confirmed": Confidence.CONFIRMED,
    "high": Confidence.HIGH,
    "medium": Confidence.MEDIUM,
    "low": Confidence.LOW,
}


def parse_risk(value: str | None) -> Risk:
    """ZAP reports risk as e.g. 'High' or 'Medium (Suspicious)'."""
    if not value:
        return Risk.INFORMATIONAL
    key = value.split("(")[0].strip().lower()
    return _RISK_LOOKUP.get(key, Risk.INFORMATIONAL)


def parse_confidence(value: str | None) -> Confidence:
    if not value:
        return Confidence.LOW
    return _CONFIDENCE_LOOKUP.get(value.strip().lower(), Confidence.LOW)


def risk_sort_key(risk: Risk) -> int:
    return RISK_ORDER.index(risk)
