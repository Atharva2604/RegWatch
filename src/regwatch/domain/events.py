"""Domain Events representing critical state transitions in the compliance lifecycle."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from regwatch.domain.models import Verdict


@dataclass(frozen=True)
class DomainEvent:
    """Base event contract."""
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class DocumentDiscovered(DomainEvent):
    """Fired when a new regulatory item is first spotted in a listing."""
    source_key: str = ""
    url: str = ""
    legal_type: str = ""
    title: str = ""


@dataclass(frozen=True)
class DocumentChanged(DomainEvent):
    """Fired when an existing regulation's content hash changes."""
    regulation_id: int = 0
    version_no: int = 1
    content_hash: str = ""
    source_key: str = ""


@dataclass(frozen=True)
class ObligationsExtracted(DomainEvent):
    """Fired when LLM successfully extracts structured obligations from a document version."""
    regulation_id: int = 0
    version_id: int = 0
    obligation_count: int = 0


@dataclass(frozen=True)
class PolicyChanged(DomainEvent):
    """Fired when a company modifies or creates an internal policy rule."""
    company_id: int = 0
    policy_id: int = 0
    category: str = ""


@dataclass(frozen=True)
class ComplianceChecked(DomainEvent):
    """Fired when a policy is evaluated against an obligation."""
    check_id: int = 0
    company_id: int = 0
    obligation_id: int = 0
    verdict: Verdict = Verdict.NEEDS_REVIEW
    score_level: str = "medium"


@dataclass(frozen=True)
class AlertTriggered(DomainEvent):
    """Fired when a critical or high-risk compliance alert is scheduled."""
    alert_id: int = 0
    company_id: int = 0
    channel: str = ""
    level: str = ""
