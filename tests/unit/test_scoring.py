"""Unit tests for the deterministic risk calculation engine."""

from datetime import date, timedelta
from regwatch.domain.models import RiskLevel, Verdict
from regwatch.domain.scoring import calculate_risk


def test_compliant_verdict_yields_low_risk() -> None:
    score = calculate_risk(
        compliance_check_id=1,
        verdict=Verdict.COMPLIANT,
        category="cyber_security",
    )
    assert score.level == RiskLevel.LOW
    assert score.score_value == 1.0
    assert score.severity == 1


def test_non_compliant_cyber_security_overdue_yields_critical() -> None:
    today = date(2026, 10, 22)
    effective_past = today - timedelta(days=5)

    score = calculate_risk(
        compliance_check_id=2,
        verdict=Verdict.NON_COMPLIANT,
        category="cyber_security",
        effective_date=effective_past,
        current_date=today,
        scope_multiplier=4,
    )
    assert score.level == RiskLevel.CRITICAL
    assert score.severity == 5
    assert score.urgency == 5
    assert score.score_value >= 4.0


def test_needs_review_medium_category_yields_medium_risk() -> None:
    today = date(2026, 10, 22)
    effective_future = today + timedelta(days=60)

    score = calculate_risk(
        compliance_check_id=3,
        verdict=Verdict.NEEDS_REVIEW,
        category="disclosures",
        effective_date=effective_future,
        current_date=today,
        scope_multiplier=2,
    )
    assert score.level in {RiskLevel.LOW, RiskLevel.MEDIUM}
    assert score.score_value < 3.0
