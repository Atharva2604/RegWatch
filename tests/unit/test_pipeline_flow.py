"""End-to-end unit test of the application pipeline flow using Fakes."""

from regwatch.bootstrap import build_test_container
from regwatch.domain.models import LegalType, ListingItem


def test_full_pipeline_ingest_detect_extract_compare() -> None:
    container = build_test_container()

    # 1. Ingest listing item
    items = [
        ListingItem(
            source_key="sebi",
            url="https://www.sebi.gov.in/legal/circulars/test_cyber.html",
            title="SEBI Master Circular on Cyber Security Framework",
            legal_type=LegalType.CIRCULAR,
        )
    ]
    summary = container.ingest_uc.execute(items)
    assert summary["items_seen"] == 1
    assert summary["jobs_enqueued"] == 1

    # 2. Worker claims detect_change job
    job1 = container.job_queue.claim_next("worker-test")
    assert job1 is not None
    assert job1.job_type == "detect_change"

    # Simulate fetcher text for this document
    container.doc_repo.save_document(
        container.doc_repo.get_by_url("https://www.sebi.gov.in/legal/circulars/test_cyber.html")
    )
    result1 = container.dispatcher.handle(job1)
    container.job_queue.mark_completed(job1.id)
    assert result1["status"] in {"updated", "unchanged"}

    # 3. Worker claims extract_obligations job
    job2 = container.job_queue.claim_next("worker-test")
    assert job2 is not None
    assert job2.job_type == "extract_obligations"

    result2 = container.dispatcher.handle(job2)
    container.job_queue.mark_completed(job2.id)
    assert result2["obligations_extracted"] >= 1

    # 4. Worker claims compare_obligation job
    job3 = container.job_queue.claim_next("worker-test")
    assert job3 is not None
    assert job3.job_type == "compare_obligation"

    result3 = container.dispatcher.handle(job3)
    container.job_queue.mark_completed(job3.id)
    assert result3["checks_created"] >= 1

    # 5. Worker claims score_and_alert job
    job4 = container.job_queue.claim_next("worker-test")
    assert job4 is not None
    assert job4.job_type == "score_and_alert"

    result4 = container.dispatcher.handle(job4)
    container.job_queue.mark_completed(job4.id)
    assert result4["status"] in {"alert_dispatched", "low_risk_no_alert"}
