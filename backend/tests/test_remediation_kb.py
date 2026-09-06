from app.services.remediation_kb import remediation_for


def test_curated_entry_takes_precedence_over_zap_text():
    text, curated = remediation_for("40018", "ZAP generic advice")
    assert curated is True
    assert "parameterised queries" in text


def test_falls_back_to_zap_solution_when_not_curated():
    text, curated = remediation_for("99999", "ZAP generic advice")
    assert curated is False
    assert text == "ZAP generic advice"


def test_handles_missing_plugin_id_and_solution():
    text, curated = remediation_for(None, None)
    assert curated is False
    assert text
