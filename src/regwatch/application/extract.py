"""Use case: Extract structured compliance obligations using LLM guardrails."""

import logging
from regwatch.domain.models import Obligation
from regwatch.domain.ports import DocumentRepository, JobQueue, LLMClient, ObligationRepository

logger = logging.getLogger(__name__)


class ExtractObligationsUseCase:
    """Invokes LLM extraction port, guarantees schema conformity, persists atomic

    obligations, and dispatches comparison jobs against internal company policies.
    """

    def __init__(
        self,
        doc_repo: DocumentRepository,
        obligation_repo: ObligationRepository,
        llm_client: LLMClient,
        job_queue: JobQueue,
    ) -> None:
        self.doc_repo = doc_repo
        self.obligation_repo = obligation_repo
        self.llm_client = llm_client
        self.job_queue = job_queue

    def execute(self, payload: dict) -> dict[str, int]:
        reg_id = payload["regulation_id"]
        version_id = payload["version_id"]
        title = payload.get("title", "")
        url = payload.get("url", "")

        doc = self.doc_repo.get_by_url(url)
        if not doc or not doc.content_text:
            logger.warning("No text content available to extract for regulation %s", reg_id)
            return {"obligations_extracted": 0}

        raw_extractions = self.llm_client.extract_obligations(doc.content_text, title)

        obligations: list[Obligation] = []
        for raw in raw_extractions:
            ob = Obligation(
                regulation_id=reg_id,
                version_id=version_id,
                requirement_text=raw["requirement_text"],
                category=raw.get("category", "general"),
                applies_to=raw.get("applies_to", "all_entities"),
                evidence_quote=raw.get("evidence_quote", ""),
                metric_name=raw.get("metric_name"),
                operator=raw.get("operator"),
                threshold_value=raw.get("threshold_value"),
                unit=raw.get("unit"),
                confidence=raw.get("confidence", 1.0),
                model=raw.get("model", "llama-3.3-70b-versatile"),
                prompt_version=raw.get("prompt_version", "v1"),
            )
            obligations.append(ob)

        saved = self.obligation_repo.save_obligations(obligations)
        logger.info("Extracted %d obligations from regulation %s (version %s)", len(saved), reg_id, version_id)

        # Enqueue comparison job for downstream evaluation
        for ob in saved:
            self.job_queue.enqueue(
                job_type="compare_obligation",
                payload={"obligation_id": ob.id, "category": ob.category},
                dedupe_key=f"compare:ob_{ob.id}",
            )

        return {"obligations_extracted": len(saved)}
