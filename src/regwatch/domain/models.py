"""Canonical Domain Models for RegWatch.

These immutable models define the core language of regulatory compliance monitoring.
They act as an Anti-Corruption Layer (ACL) against messy external regulator formats.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class LegalType(str, Enum):
    """Canonical regulatory legal instrument types."""
    ACT = "act"
    RULE = "rule"
    REGULATION = "regulation"
    CIRCULAR = "circular"
    MASTER_CIRCULAR = "master_circular"
    GUIDELINE = "guideline"
    GENERAL_ORDER = "general_order"
    OTHER = "other"


class Verdict(str, Enum):
    """Compliance assessment verdicts."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    NO_POLICY = "no_policy"


class RiskLevel(str, Enum):
    """Calculated risk categorization levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ListingItem:
    """Anti-Corruption Layer record produced by source listings scrapers.
    
    Downstream pipeline stages only interact with this standardized representation,
    never with raw website HTML tags or irregular query structures.
    """
    source_key: str
    url: str
    title: str
    legal_type: LegalType
    published_date: date | None = None
    external_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FetchedContent:
    """Raw content extracted from a regulatory listing URL."""
    url: str
    text: str
    content_type: str  # "html" | "pdf"
    needs_ocr: bool = False
    raw_sha256: str = ""
    raw_storage_path: str | None = None


@dataclass
class LegalDocument:
    """Canonical domain representation of a regulatory instrument."""
    source_key: str
    url: str
    title: str
    legal_type: LegalType
    published_date: date | None = None
    reference_number: str | None = None
    department: str | None = None
    content_text: str = ""
    content_hash: str = ""
    first_seen_at: datetime | None = None
    last_checked_at: datetime | None = None
    last_changed_at: datetime | None = None
    status: str = "active"
    check_class: str = "fresh"  # fresh | standing | foundational
    id: int | None = None
    current_version_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentVersion:
    """Immutable snapshot of a regulatory document at a specific point in time."""
    regulation_id: int
    version_no: int
    content_text: str
    content_hash: str
    diff_summary: str | None = None
    raw_sha256: str | None = None
    raw_storage_path: str | None = None
    created_at: datetime | None = None
    id: int | None = None


@dataclass(frozen=True)
class Obligation:
    """Atomic, structured compliance requirement extracted from a legal document."""
    regulation_id: int
    requirement_text: str
    category: str  # e.g., "incident_reporting", "kyc", "data_retention"
    applies_to: str  # e.g., "stock_broker", "depository", "all_regulated_entities"
    evidence_quote: str  # verbatim quote from regulatory text for 100% auditability
    metric_name: str | None = None  # e.g., "incident_report_hours"
    operator: str | None = None  # "<=", ">=", "=", "must", "must_not"
    threshold_value: float | None = None
    unit: str | None = None  # "hours", "days", "inr"
    effective_date: date | None = None
    confidence: float = 1.0
    model: str = "unknown"
    prompt_version: str = "v1"
    status: str = "active"
    version_id: int | None = None
    fingerprint: str | None = None
    id: int | None = None


@dataclass(frozen=True)
class CompanyPolicy:
    """Internal compliance policy rule maintained by a regulated entity."""
    company_id: int
    category: str
    policy_text: str
    title: str = ""
    metric_name: str | None = None
    value: float | None = None
    unit: str | None = None
    id: int | None = None


@dataclass(frozen=True)
class ComplianceCheck:
    """Evaluation verdict of an obligation against a company policy."""
    obligation_id: int
    company_policy_id: int | None
    company_id: int
    verdict: Verdict
    confidence: float
    explanation: str
    method: str  # "rule_based" | "llm_judge"
    triggered_by: str = "regulation_change"
    inputs_hash: str = ""
    id: int | None = None


@dataclass(frozen=True)
class RiskScore:
    """Multi-dimensional risk score quantifying regulatory impact."""
    compliance_check_id: int
    severity: int  # 1 to 5
    urgency: int   # 1 to 5
    scope: int     # 1 to 5
    level: RiskLevel
    score_value: float
    reason: str = ""
    id: int | None = None


@dataclass(frozen=True)
class Alert:
    """Actionable compliance notification dispatched to stakeholders."""
    compliance_check_id: int
    company_id: int
    channel: str  # "email" | "telegram" | "in_app"
    dedupe_key: str
    status: str = "pending"  # "pending" | "sent" | "failed"
    lifecycle: str = "open"  # "open" | "acknowledged" | "remediated" | "closed"
    id: int | None = None


@dataclass
class Job:
    """Persistent unit of work managed by the distributed job queue."""
    job_type: str
    payload: dict[str, Any]
    dedupe_key: str | None = None
    status: str = "pending"  # "pending" | "running" | "done" | "failed" | "dead"
    attempts: int = 0
    max_attempts: int = 5
    run_after: datetime | None = None
    locked_at: datetime | None = None
    last_error: str | None = None
    run_id: int | None = None
    id: int | None = None
