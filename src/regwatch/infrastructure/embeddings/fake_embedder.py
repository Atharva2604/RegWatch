"""Embedding providers (384-dimension vector representations for pgvector)."""

import hashlib
from regwatch.domain.ports import Embedder


class FakeEmbedder(Embedder):
    """Deterministic 384-dimension vector embedder for test suites and offline execution."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        # Generate deterministic float vector from text sha256
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
        return [(float((seed + i) % 100) / 100.0) for i in range(self.dimension)]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
