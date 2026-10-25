"""Pure deterministic risk calculation engine."""

from datetime import date
from regwatch.domain.models import RiskLevel, RiskScore, Verdict


def calculate_risk(
    compliance_check_id: int,
    verdict: Verdict,
    category: str,
    effective_date: date | None = None,
    current_date: date | None = None,
    scope_multiplier: int = 3,
) -> RiskScore:
    """Calculate multi-dimensional risk score as a pure deterministic function.
    
    Weights:
      - Severity (45%): Core impact of regulatory non-compliance in the category.
      - Urgency (35%): Closeness of the regulatory deadline.
      - Scope (20%): Breadth of business impact across systems/entities.
    """
    if verdict == Verdict.COMPLIANT:
        return RiskScore(
            compliance_check_id=compliance_check_id,
            severity=1,
            urgency=1,
            scope=1,
            level=RiskLevel.LOW,
            score_value=1.0,
            reason="Entity is fully compliant with obligation requirements.",
        )

    # 1. Severity calculation based on domain sensitivity
    high_impact_categories = {"incident_reporting", "cyber_security", "capital_adequacy", "kyc_aml"}
    medium_impact_categories = {"data_retention", "disclosures", "audit_log"}

    if category in high_impact_categories:
        severity = 5 if verdict == Verdict.NON_COMPLIANT else 4
    elif category in medium_impact_categories:
        severity = 3
    else:
        severity = 2

    # 2. Urgency calculation based on effective deadline
    if effective_date and current_date:
        days_remaining = (effective_date - current_date).days
        if days_remaining <= 0:
            urgency = 5  # In effect now or overdue
        elif days_remaining <= 7:
            urgency = 4  # Within a week
        elif days_remaining <= 30:
            urgency = 3  # Within a month
        else:
            urgency = 2  # Future date
    else:
        # Default urgency when date unspecified
        urgency = 4 if severity >= 4 else 2

    # 3. Scope (1 to 5)
    scope = max(1, min(5, scope_multiplier))

    # Composite weighted score (1.0 to 5.0)
    score_value = round((0.45 * severity) + (0.35 * urgency) + (0.20 * scope), 2)

    # Risk level classification threshold
    if score_value >= 4.0:
        level = RiskLevel.CRITICAL
    elif score_value >= 3.0:
        level = RiskLevel.HIGH
    elif score_value >= 2.0:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    reason = (
        f"Verdict: {verdict.value.upper()} | Severity={severity}/5 ({category}), "
        f"Urgency={urgency}/5, Scope={scope}/5 -> Composite Score={score_value}"
    )

    return RiskScore(
        compliance_check_id=compliance_check_id,
        severity=severity,
        urgency=urgency,
        scope=scope,
        level=level,
        score_value=score_value,
        reason=reason,
    )
