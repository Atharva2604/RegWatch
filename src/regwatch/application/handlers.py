"""Pipes & Filters Stage Handler (Job Dispatcher).

Connects asynchronous queue tasks to specific application use cases.
"""

import logging
from typing import Any
from regwatch.application.alert import ScoreAndAlertUseCase
from regwatch.application.compare import CompareObligationUseCase
from regwatch.application.detect import DetectChangeUseCase
from regwatch.application.extract import ExtractObligationsUseCase
from regwatch.domain.models import Job

logger = logging.getLogger(__name__)


class JobDispatcher:
    """Dispatches background jobs to their corresponding use case handlers."""

    def __init__(
        self,
        detect_uc: DetectChangeUseCase,
        extract_uc: ExtractObligationsUseCase,
        compare_uc: CompareObligationUseCase,
        alert_uc: ScoreAndAlertUseCase,
    ) -> None:
        self.detect_uc = detect_uc
        self.extract_uc = extract_uc
        self.compare_uc = compare_uc
        self.alert_uc = alert_uc

    def handle(self, job: Job) -> dict[str, Any]:
        """Dispatch a claimed job to its application use-case handler."""
        logger.info("Executing job id=%s type='%s'", job.id, job.job_type)

        if job.job_type == "detect_change":
            return self.detect_uc.execute(job.payload)
        elif job.job_type == "extract_obligations":
            return self.extract_uc.execute(job.payload)
        elif job.job_type == "compare_obligation":
            return self.compare_uc.execute(job.payload)
        elif job.job_type == "score_and_alert":
            return self.alert_uc.execute(job.payload)
        else:
            raise ValueError(f"Unknown job_type: '{job.job_type}'")
