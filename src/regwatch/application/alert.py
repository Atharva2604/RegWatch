"""Use case: Risk Scoring and Alerting."""

import logging
from datetime import date
from regwatch.domain.models import Alert, RiskLevel, Verdict
from regwatch.domain.ports import CheckRepository, Notifier
from regwatch.domain.scoring import calculate_risk

logger = logging.getLogger(__name__)


class ScoreAndAlertUseCase:
    """Computes risk severity/urgency/scope scores for compliance verdicts

    and dispatches deduplicated alerts for non-compliant or high-risk findings.
    """

    def __init__(self, check_repo: CheckRepository, notifier: Notifier) -> None:
        self.check_repo = check_repo
        self.notifier = notifier

    def execute(self, payload: dict) -> dict[str, str]:
        check_id = payload["compliance_check_id"]
        company_id = payload.get("company_id", 1)

        # Calculate pure domain risk score
        risk_score = calculate_risk(
            compliance_check_id=check_id,
            verdict=Verdict.NON_COMPLIANT,
            category="cyber_security",
            current_date=date.today(),
        )
        self.check_repo.save_risk_score(risk_score)

        if risk_score.level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            dedupe_key = f"alert:{company_id}:{check_id}:email"
            alert = Alert(
                compliance_check_id=check_id,
                company_id=company_id,
                channel="email",
                dedupe_key=dedupe_key,
                status="pending",
            )
            saved_alert = self.check_repo.save_alert(alert)

            subject = f"[{risk_score.level.value.upper()}] Regulatory Non-Compliance Detected"
            body = (
                f"Attention Compliance Officer,\n\n"
                f"A regulatory compliance risk has been detected.\n"
                f"Details: {risk_score.reason}\n"
                f"Score: {risk_score.score_value}/5.0\n"
            )
            success = self.notifier.send_alert(saved_alert, subject=subject, body=body)
            return {"status": "alert_dispatched" if success else "alert_failed", "level": risk_score.level.value}

        return {"status": "low_risk_no_alert", "level": risk_score.level.value}
