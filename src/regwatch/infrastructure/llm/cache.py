"""LLM response cache based on content hash, prompt version, and model."""

import hashlib
import json
from typing import Any


def compute_cache_key(content_hash: str, prompt_version: str, model: str) -> str:
    """Compute deterministic cache key for LLM queries."""
    key_src = f"{content_hash}:{prompt_version}:{model}"
    return hashlib.sha256(key_src.encode("utf-8")).hexdigest()


class LLMCache:
    """Two-tier cache (in-memory + database) for LLM inferences."""

    def __init__(self, supabase_client: Any = None) -> None:
        self.client = supabase_client
        self._memory_cache: dict[str, Any] = {}

    def get(self, cache_key: str) -> Any | None:
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        if self.client:
            try:
                res = self.client.table("llm_cache").select("response").eq("cache_key", cache_key).execute()
                if res.data:
                    val = res.data[0]["response"]
                    self._memory_cache[cache_key] = val
                    return val
            except Exception:
                pass

        return None

    def set(self, cache_key: str, response: Any, model: str, prompt_version: str) -> None:
        self._memory_cache[cache_key] = response
        if self.client:
            try:
                self.client.table("llm_cache").upsert({
                    "cache_key": cache_key,
                    "response": response,
                    "model": model,
                    "prompt_version": prompt_version,
                }).execute()
            except Exception:
                pass
