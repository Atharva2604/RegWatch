"""Deterministic Fake LLM client for tests."""

from typing import Any
from regwatch.domain.models import CompanyPolicy, Obligation
from regwatch.domain.ports import LLMClient


class FakeLLMClient(LLMClient):
    """Deterministic fake LLM client enabling 100% offline unit and contract testing."""

    def __init__(self, canned_obligations: list[dict[str, Any]] | None = None) -> None:
        self.canned_obligations = canned_obligations or [
            {
                "requirement_text": "Regulated entities must report cyber incidents to SEBI within 6 hours of discovery.",
                "category": "cyber_security",
                "applies_to": "all_entities",
                "evidence_quote": "report cyber incidents to SEBI within 6 hours",
                "metric_name": "incident_report_hours",
                "operator": "<=",
                "threshold_value": 6.0,
                "unit": "hours",
                "confidence": 0.98,
                "model": "fake-llama",
                "prompt_version": "v1",
            }
        ]

    def extract_obligations(self, text: str, document_title: str) -> list[dict[str, Any]]:
        return self.canned_obligations

    def evaluate_compliance(self, obligation: Obligation, policy: CompanyPolicy) -> dict[str, Any]:
        return {
            "verdict": "non_compliant",
            "confidence": 0.95,
            "explanation": f"Policy allows {policy.value} {policy.unit}, but obligation demands {obligation.threshold_value} {obligation.unit}.",
        }
