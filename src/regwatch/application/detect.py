"""Use case: Content Acquisition, Normalization & Change Detection."""

import hashlib
import logging
from datetime import datetime, timezone
from regwatch.domain.models import DocumentVersion, LegalDocument
from regwatch.domain.ports import DocumentRepository, Fetcher, JobQueue

logger = logging.getLogger(__name__)


def compute_sha256(content: str) -> str:
    """Compute deterministic SHA-256 hash of normalized text."""
    # Normalize whitespace to avoid spurious diffs due to indentation/newlines
    normalized = " ".join(content.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DetectChangeUseCase:
    """Fetches full document text, normalizes, detects content updates via cryptographic hashes,

    and triggers downstream extraction only on meaningful changes.
    """

    def __init__(
        self,
        doc_repo: DocumentRepository,
        fetcher: Fetcher,
        job_queue: JobQueue,
    ) -> None:
        self.doc_repo = doc_repo
        self.fetcher = fetcher
        self.job_queue = job_queue

    def execute(self, payload: dict) -> dict[str, str]:
        url = payload["url"]
        doc_id = payload.get("document_id")

        doc = self.doc_repo.get_by_url(url)
        if not doc:
            logger.warning("Document not found for URL: %s", url)
            return {"status": "not_found"}

        # Fetch actual body / PDF content
        fetched = self.fetcher.fetch_document_content(url)
        new_hash = compute_sha256(fetched.text)

        if doc.content_hash == new_hash:
            logger.info("Document unchanged: %s (hash: %s)", doc.title, new_hash[:10])
            doc.last_checked_at = datetime.now(timezone.utc)
            self.doc_repo.save_document(doc)
            return {"status": "unchanged", "hash": new_hash}

        # Content is either brand new or changed!
        is_first_version = not bool(doc.content_hash)
        logger.info(
            "%s detected for document: %s (new hash: %s)",
            "Initial publication" if is_first_version else "Regulatory change",
            doc.title,
            new_hash[:10],
        )

        now = datetime.now(timezone.utc)
        doc.content_text = fetched.text
        doc.content_hash = new_hash
        doc.last_checked_at = now
        doc.last_changed_at = now

        # Save document to obtain updated row
        updated_doc = self.doc_repo.save_document(doc)

        # Create new version record
        version_no = (doc.current_version_id or 0) + 1
        version = DocumentVersion(
            regulation_id=updated_doc.id or 0,
            version_no=version_no,
            content_text=fetched.text,
            content_hash=new_hash,
            raw_sha256=fetched.raw_sha256,
            raw_storage_path=fetched.raw_storage_path,
            created_at=now,
        )
        saved_version = self.doc_repo.save_version(version)
        updated_doc.current_version_id = saved_version.id
        self.doc_repo.save_document(updated_doc)

        # Enqueue downstream LLM extraction job
        self.job_queue.enqueue(
            job_type="extract_obligations",
            payload={
                "regulation_id": updated_doc.id,
                "version_id": saved_version.id,
                "title": updated_doc.title,
                "legal_type": updated_doc.legal_type.value,
                "url": updated_doc.url,
            },
            dedupe_key=f"extract:{updated_doc.id}:v{saved_version.id}",
        )

        return {"status": "updated", "version_id": str(saved_version.id), "hash": new_hash}
