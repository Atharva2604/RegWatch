"""Composition Root (Dependency Injection).

This is the SINGLE location in the entire codebase where concrete infrastructure
adapters are instantiated and wired into domain ports and application use cases.
Application and Domain layers have zero knowledge of this composition.
"""

from dataclasses import dataclass
from typing import Any
from supabase import Client, create_client
from regwatch.application.alert import ScoreAndAlertUseCase
from regwatch.application.compare import CompareObligationUseCase
from regwatch.application.detect import DetectChangeUseCase
from regwatch.application.extract import ExtractObligationsUseCase
from regwatch.application.handlers import JobDispatcher
from regwatch.application.ingest import IngestListingUseCase
from regwatch.domain.ports import (
    CheckRepository,
    DocumentRepository,
    Fetcher,
    JobQueue,
    LLMClient,
    Notifier,
    ObligationRepository,
    PolicyRepository,
)
from regwatch.infrastructure.db.queue import PostgresJobQueue
from regwatch.infrastructure.db.supabase_repo import (
    SupabaseCheckRepository,
    SupabaseDocumentRepository,
    SupabaseObligationRepository,
    SupabasePolicyRepository,
)
from regwatch.infrastructure.fetch.circuit_breaker import CircuitBreaker
from regwatch.infrastructure.fetch.fake_fetcher import FakeFetcher
from regwatch.infrastructure.fetch.http_fetcher import HttpFetcher
from regwatch.infrastructure.fetch.ratelimit import TokenBucketRateLimiter
from regwatch.infrastructure.llm.client import UnifiedLLMClient
from regwatch.infrastructure.llm.fake_provider import FakeLLMClient
from regwatch.infrastructure.notify.fake_notifier import FakeNotifier
from regwatch.settings import Settings, get_settings


@dataclass
class AppContainer:
    """Dependency injection container holding configured ports and use cases."""
    settings: Settings
    fetcher: Fetcher
    doc_repo: DocumentRepository
    obligation_repo: ObligationRepository
    policy_repo: PolicyRepository
    check_repo: CheckRepository
    job_queue: JobQueue
    llm_client: LLMClient
    notifier: Notifier

    # Application Use Cases
    ingest_uc: IngestListingUseCase
    detect_uc: DetectChangeUseCase
    extract_uc: ExtractObligationsUseCase
    compare_uc: CompareObligationUseCase
    alert_uc: ScoreAndAlertUseCase
    dispatcher: JobDispatcher


def build_container(settings: Settings | None = None) -> AppContainer:
    """Build production container wired to real Supabase, HTTP, and Groq."""
    settings = settings or get_settings()

    # Supabase Client
    supabase: Client | None = None
    if settings.supabase_url and settings.supabase_key:
        try:
            supabase = create_client(settings.supabase_url, settings.supabase_key)
        except Exception:
            pass

    # Infrastructure Ports
    rate_limiter = TokenBucketRateLimiter(rate_per_second=settings.rate_limit_rps)
    circuit_breaker = CircuitBreaker()
    fetcher = HttpFetcher(
        user_agent=settings.user_agent,
        timeout_seconds=settings.request_timeout_seconds,
        rate_limiter=rate_limiter,
        circuit_breaker=circuit_breaker,
    )

    doc_repo = SupabaseDocumentRepository(supabase)
    obligation_repo = SupabaseObligationRepository(supabase)
    policy_repo = SupabasePolicyRepository(supabase)
    check_repo = SupabaseCheckRepository(supabase)
    job_queue = PostgresJobQueue(supabase)

    llm_client = UnifiedLLMClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
    )
    notifier = FakeNotifier()

    # Application Use Cases
    ingest_uc = IngestListingUseCase(doc_repo=doc_repo, job_queue=job_queue)
    detect_uc = DetectChangeUseCase(doc_repo=doc_repo, fetcher=fetcher, job_queue=job_queue)
    extract_uc = ExtractObligationsUseCase(
        doc_repo=doc_repo,
        obligation_repo=obligation_repo,
        llm_client=llm_client,
        job_queue=job_queue,
    )
    compare_uc = CompareObligationUseCase(
        obligation_repo=obligation_repo,
        policy_repo=policy_repo,
        check_repo=check_repo,
        llm_client=llm_client,
        job_queue=job_queue,
    )
    alert_uc = ScoreAndAlertUseCase(check_repo=check_repo, notifier=notifier)
    dispatcher = JobDispatcher(
        detect_uc=detect_uc,
        extract_uc=extract_uc,
        compare_uc=compare_uc,
        alert_uc=alert_uc,
    )

    return AppContainer(
        settings=settings,
        fetcher=fetcher,
        doc_repo=doc_repo,
        obligation_repo=obligation_repo,
        policy_repo=policy_repo,
        check_repo=check_repo,
        job_queue=job_queue,
        llm_client=llm_client,
        notifier=notifier,
        ingest_uc=ingest_uc,
        detect_uc=detect_uc,
        extract_uc=extract_uc,
        compare_uc=compare_uc,
        alert_uc=alert_uc,
        dispatcher=dispatcher,
    )


def build_test_container() -> AppContainer:
    """Build isolated in-memory container using fakes for fast unit and contract testing."""
    settings = Settings(environment="test")
    doc_repo = SupabaseDocumentRepository(None)
    obligation_repo = SupabaseObligationRepository(None)
    policy_repo = SupabasePolicyRepository(None)
    check_repo = SupabaseCheckRepository(None)
    job_queue = PostgresJobQueue(None)
    llm_client = FakeLLMClient()
    notifier = FakeNotifier()

    fetcher = FakeFetcher()

    ingest_uc = IngestListingUseCase(doc_repo=doc_repo, job_queue=job_queue)
    detect_uc = DetectChangeUseCase(doc_repo=doc_repo, fetcher=fetcher, job_queue=job_queue)
    extract_uc = ExtractObligationsUseCase(
        doc_repo=doc_repo,
        obligation_repo=obligation_repo,
        llm_client=llm_client,
        job_queue=job_queue,
    )
    compare_uc = CompareObligationUseCase(
        obligation_repo=obligation_repo,
        policy_repo=policy_repo,
        check_repo=check_repo,
        llm_client=llm_client,
        job_queue=job_queue,
    )
    alert_uc = ScoreAndAlertUseCase(check_repo=check_repo, notifier=notifier)
    dispatcher = JobDispatcher(
        detect_uc=detect_uc,
        extract_uc=extract_uc,
        compare_uc=compare_uc,
        alert_uc=alert_uc,
    )

    return AppContainer(
        settings=settings,
        fetcher=fetcher,
        doc_repo=doc_repo,
        obligation_repo=obligation_repo,
        policy_repo=policy_repo,
        check_repo=check_repo,
        job_queue=job_queue,
        llm_client=llm_client,
        notifier=notifier,
        ingest_uc=ingest_uc,
        detect_uc=detect_uc,
        extract_uc=extract_uc,
        compare_uc=compare_uc,
        alert_uc=alert_uc,
        dispatcher=dispatcher,
    )
