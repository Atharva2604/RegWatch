"""Domain Ports (Hexagonal Architecture / Inversion of Control).

All external integrations (databases, LLM APIs, HTTP clients, queues) are abstracted
into these typing.Protocol interfaces. Domain and Application layers depend exclusively
on these contracts, never on concrete vendor SDKs.
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Any, Protocol

from regwatch.domain.models import (
    Alert,
    CompanyPolicy,
    ComplianceCheck,
    DocumentVersion,
    FetchedContent,
    Job,
    LegalDocument,
    ListingItem,
    Obligation,
    RiskScore,
)


class DocumentRepository(Protocol):
    """Port for persisting and retrieving regulatory documents and versions."""

    def get_by_url(self, url: str) -> LegalDocument | None: ...
    def save_document(self, document: LegalDocument) -> LegalDocument: ...
    def save_version(self, version: DocumentVersion) -> DocumentVersion: ...
    def list_unprocessed(self, limit: int = 10) -> list[LegalDocument]: ...
    def update_check_schedule(self, doc_id: int, next_check: datetime) -> None: ...


class ObligationRepository(Protocol):
    """Port for managing atomic extracted obligations."""

    def save_obligations(self, obligations: list[Obligation]) -> list[Obligation]: ...
    def get_by_regulation_version(self, version_id: int) -> list[Obligation]: ...
    def get_by_category(self, category: str) -> list[Obligation]: ...


class PolicyRepository(Protocol):
    """Port for accessing company policies."""

    def get_policies_for_company(self, company_id: int) -> list[CompanyPolicy]: ...
    def get_policies_by_category(self, company_id: int, category: str) -> list[CompanyPolicy]: ...


class CheckRepository(Protocol):
    """Port for recording compliance checks, risk scores, and alerts."""

    def get_check_by_inputs_hash(self, inputs_hash: str) -> ComplianceCheck | None: ...
    def save_check(self, check: ComplianceCheck) -> ComplianceCheck: ...
    def save_risk_score(self, risk_score: RiskScore) -> RiskScore: ...
    def save_alert(self, alert: Alert) -> Alert: ...


class JobQueue(Protocol):
    """Port for persistent, transactional task management (Pipes & Filters)."""

    def enqueue(self, job_type: str, payload: dict[str, Any], dedupe_key: str | None = None) -> Job: ...
    def claim_next(self, worker_id: str) -> Job | None: ...
    def mark_completed(self, job_id: int) -> None: ...
    def mark_failed(self, job_id: int, error: str, retry_after_seconds: int = 60) -> None: ...


class Fetcher(Protocol):
    """Port for polite HTTP/PDF content acquisition."""

    def fetch_listing_page(self, url: str) -> str: ...
    def fetch_paged_listing(self, url: str, page_num: int) -> str: ...
    def fetch_document_content(self, url: str) -> FetchedContent: ...


class LLMClient(Protocol):
    """Port for structured JSON generation with guaranteed schema validation."""

    def extract_obligations(self, text: str, document_title: str) -> list[dict[str, Any]]: ...
    def evaluate_compliance(
        self,
        obligation: Obligation,
        policy: CompanyPolicy,
    ) -> dict[str, Any]: ...


class Embedder(Protocol):
    """Port for semantic vector representations (pgvector compatible)."""

    def embed_text(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class Notifier(Protocol):
    """Port for dispatching compliance alerts across channels."""

    def send_alert(self, alert: Alert, subject: str, body: str) -> bool: ...


class Clock(Protocol):
    """Port for deterministic time evaluation."""

    def now(self) -> datetime: ...
