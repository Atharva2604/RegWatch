"""Domain exception hierarchy."""


class RegWatchError(Exception):
    """Base exception for all domain and system errors in RegWatch."""


class DomainError(RegWatchError):
    """Raised when an operation violates core domain rules or state constraints."""


class FetchError(RegWatchError):
    """Raised when an external source fails to fetch within SLA or returns HTTP errors."""


class RateLimitError(FetchError):
    """Raised when request rate limits for an upstream regulator are exceeded."""


class CircuitBreakerOpenError(FetchError):
    """Raised when circuit breaker trips due to repeated upstream failures."""


class ObligationParsingError(DomainError):
    """Raised when an LLM or parser produces output that cannot be normalized."""


class QuarantineError(DomainError):
    """Raised when content fails quality gates and must be sent to quarantine."""
