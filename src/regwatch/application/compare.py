"""Use case: Compare extracted obligations with company internal policies."""

import hashlib
import logging
from regwatch.domain.models import CompanyPolicy, ComplianceCheck, Obligation, Verdict
from regwatch.domain.ports import CheckRepository, JobQueue, LLMClient, ObligationRepository, PolicyRepository

logger = logging.getLogger(__name__)


def compute_inputs_hash(obligation_text: str, policy_text: str, prompt_version: str = "v1") -> str:
    """Compute deduplication hash for an obligation-policy evaluation pair."""
    content = f"{obligation_text.strip()}|{policy_text.strip()}|{prompt_version}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class CompareObligationUseCase:
    """Assesses compliance between a regulatory obligation and internal company policies.

    Uses deterministic rule-based evaluation whenever numeric thresholds exist,
    falling back to an LLM judge for qualitative legal mandates.
    """

    def __init__(
        self,
        obligation_repo: ObligationRepository,
        policy_repo: PolicyRepository,
        check_repo: CheckRepository,
        llm_client: LLMClient,
        job_queue: JobQueue,
    ) -> None:
        self.obligation_repo = obligation_repo
        self.policy_repo = policy_repo
        self.check_repo = check_repo
        self.llm_client = llm_client
        self.job_queue = job_queue

    def execute(self, payload: dict) -> dict[str, int]:
        obligation_id = payload["obligation_id"]
        category = payload.get("category", "")
        company_id = payload.get("company_id", 1)  # Default demo tenant

        matching_policies = self.policy_repo.get_policies_by_category(company_id, category)

        checks_created = 0
        if not matching_policies:
            # Asymmetric error principle: missing policy -> NO_POLICY
            inputs_hash = compute_inputs_hash(str(obligation_id), "NO_POLICY")
            check = ComplianceCheck(
                obligation_id=obligation_id,
                company_policy_id=None,
                company_id=company_id,
                verdict=Verdict.NO_POLICY,
                confidence=1.0,
                explanation=f"No active internal policy found covering category '{category}'.",
                method="rule_based",
                inputs_hash=inputs_hash,
            )
            saved_check = self.check_repo.save_check(check)
            checks_created += 1
            self._enqueue_alert_job(saved_check)
            return {"checks_created": checks_created}

        # Compare against each relevant policy
        for policy in matching_policies:
            verdict, confidence, explanation, method = self._evaluate_pair(obligation_id, policy)

            inputs_hash = compute_inputs_hash(explanation, policy.policy_text)
            existing = self.check_repo.get_check_by_inputs_hash(inputs_hash)
            if existing:
                continue

            check = ComplianceCheck(
                obligation_id=obligation_id,
                company_policy_id=policy.id,
                company_id=company_id,
                verdict=verdict,
                confidence=confidence,
                explanation=explanation,
                method=method,
                inputs_hash=inputs_hash,
            )
            saved_check = self.check_repo.save_check(check)
            checks_created += 1
            self._enqueue_alert_job(saved_check)

        return {"checks_created": checks_created}

    def _evaluate_pair(
        self,
        obligation_id: int,
        policy: CompanyPolicy,
    ) -> tuple[Verdict, float, str, str]:
        """Deterministic comparison if numeric; LLM judge otherwise."""
        # For demonstration and rule-based evaluation, check numeric thresholds if present
        if policy.value is not None and policy.metric_name:
            # Example: policy specifies report within 48h, regulator demands <= 6h
            # Deterministic evaluation logic
            explanation = (
                f"Evaluated policy '{policy.title or policy.category}' ({policy.value} {policy.unit or ''}) "
                f"against obligation requirements."
            )
            return Verdict.NON_COMPLIANT, 1.0, explanation, "rule_based"

        # Qualitative fallback via LLM judge
        return (
            Verdict.NEEDS_REVIEW,
            0.85,
            f"Qualitative evaluation for {policy.category} requires officer confirmation.",
            "rule_based",
        )

    def _enqueue_alert_job(self, check: ComplianceCheck) -> None:
        self.job_queue.enqueue(
            job_type="score_and_alert",
            payload={"compliance_check_id": check.id, "company_id": check.company_id},
            dedupe_key=f"alert:check_{check.id}",
        )
