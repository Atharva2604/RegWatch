"""Application Layer: Orchestrates business use cases and pipeline stages.

Strict Dependency Rule:
This layer depends exclusively on regwatch.domain.
It has zero knowledge of concrete databases, HTTP libraries, or AI SDKs.
"""

from regwatch.application.alert import ScoreAndAlertUseCase
from regwatch.application.compare import CompareObligationUseCase
from regwatch.application.detect import DetectChangeUseCase
from regwatch.application.extract import ExtractObligationsUseCase
from regwatch.application.handlers import JobDispatcher
from regwatch.application.ingest import IngestListingUseCase

__all__ = [
    "CompareObligationUseCase",
    "DetectChangeUseCase",
    "ExtractObligationsUseCase",
    "IngestListingUseCase",
    "JobDispatcher",
    "ScoreAndAlertUseCase",
]
