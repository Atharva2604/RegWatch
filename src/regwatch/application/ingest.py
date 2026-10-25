"""Use case: Ingest Listings & Dispatch Detection Tasks."""

import logging
from collections.abc import Iterable
from regwatch.domain.models import LegalDocument, ListingItem
from regwatch.domain.ports import DocumentRepository, JobQueue

logger = logging.getLogger(__name__)


class IngestListingUseCase:
    """Processes canonical ListingItems from source adapters, reconciles against known

    documents, and dispatches change detection jobs.
    """

    def __init__(self, doc_repo: DocumentRepository, job_queue: JobQueue) -> None:
        self.doc_repo = doc_repo
        self.job_queue = job_queue

    def execute(self, items: Iterable[ListingItem], run_id: int | None = None) -> dict[str, int]:
        seen = 0
        enqueued = 0

        for item in items:
            seen += 1
            existing = self.doc_repo.get_by_url(item.url)

            if existing is None:
                # First time seeing this document
                doc = LegalDocument(
                    source_key=item.source_key,
                    url=item.url,
                    title=item.title,
                    legal_type=item.legal_type,
                    published_date=item.published_date,
                    reference_number=item.external_id,
                    metadata=item.metadata,
                )
                saved_doc = self.doc_repo.save_document(doc)
                doc_id = saved_doc.id
            else:
                doc_id = existing.id

            # Enqueue change detection job with idempotent dedupe key
            dedupe_key = f"detect:{item.url}"
            payload = {
                "document_id": doc_id,
                "url": item.url,
                "title": item.title,
                "source_key": item.source_key,
                "legal_type": item.legal_type.value,
                "run_id": run_id,
            }
            self.job_queue.enqueue("detect_change", payload=payload, dedupe_key=dedupe_key)
            enqueued += 1

        logger.info("Ingest complete: %d items seen, %d detection jobs enqueued", seen, enqueued)
        return {"items_seen": seen, "jobs_enqueued": enqueued}
