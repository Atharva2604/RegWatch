"""Fetch infrastructure: polite HTTP clients, rate limiters, circuit breakers, and document extractors."""

from regwatch.infrastructure.fetch.circuit_breaker import CircuitBreaker
from regwatch.infrastructure.fetch.http_fetcher import HttpFetcher
from regwatch.infrastructure.fetch.pdf_extractor import extract_text_from_pdf
from regwatch.infrastructure.fetch.ratelimit import TokenBucketRateLimiter

__all__ = [
    "CircuitBreaker",
    "HttpFetcher",
    "TokenBucketRateLimiter",
    "extract_text_from_pdf",
]
