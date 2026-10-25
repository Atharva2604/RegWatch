"""Domain layer: Core business concepts, ports, events, and pure algorithms.

Strict Dependency Rule:
This layer has ZERO dependencies on outer layers (application, infrastructure, interfaces).
"""

from regwatch.domain.errors import (
    CircuitBreakerOpenError,
    DomainError,
    FetchError,
    ObligationParsingError,
    QuarantineError,
    RateLimitError,
    RegWatchError,
)
from regwatch.domain.models import (
    Alert,
    CompanyPolicy,
    ComplianceCheck,
    DocumentVersion,
    FetchedContent,
    Job,
    LegalDocument,
    LegalType,
    ListingItem,
    Obligation,
    RiskLevel,
    RiskScore,
    Verdict,
)

__all__ = [
    "Alert",
    "CircuitBreakerOpenError",
    "CompanyPolicy",
    "ComplianceCheck",
    "DocumentVersion",
    "DomainError",
    "FetchError",
    "FetchedContent",
    "Job",
    "LegalDocument",
    "LegalType",
    "ListingItem",
    "Obligation",
    "ObligationParsingError",
    "QuarantineError",
    "RateLimitError",
    "RegWatchError",
    "RiskLevel",
    "RiskScore",
    "Verdict",
]
