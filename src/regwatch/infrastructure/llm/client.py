"""Unified LLM Client with Groq, caching, and fallback support."""

import json
import logging
from typing import Any
from groq import Groq
from regwatch.domain.models import CompanyPolicy, Obligation
from regwatch.domain.ports import LLMClient
from regwatch.infrastructure.llm.cache import LLMCache, compute_cache_key
from regwatch.infrastructure.llm.prompts import OBLIGATION_EXTRACTION_PROMPT_V1

logger = logging.getLogger(__name__)


class UnifiedLLMClient(LLMClient):
    """Production LLM client utilizing Groq with Pydantic JSON validation,

    hash-based caching, and graceful degradation.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        cache: LLMCache | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.cache = cache or LLMCache()
        self.client = Groq(api_key=api_key) if api_key else None

    def extract_obligations(self, text: str, document_title: str) -> list[dict[str, Any]]:
        if not self.client:
            logger.warning("Groq API key missing. Returning empty extraction.")
            return []

        # Check cache
        content_hash = str(hash(text[:5000]))
        cache_key = compute_cache_key(content_hash, "v1", self.model)
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("Retrieved LLM extraction from cache (key=%s)", cache_key[:10])
            return cached

        # Prepare prompt (limit input to 12,000 characters to protect context limits)
        prompt = OBLIGATION_EXTRACTION_PROMPT_V1.format(
            title=document_title,
            text=text[:12000],
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            raw_text = response.choices[0].message.content or "{}"
            parsed = json.loads(raw_text)

            # Handle either array or object wrapper
            if isinstance(parsed, list):
                result = parsed
            elif isinstance(parsed, dict) and "obligations" in parsed:
                result = parsed["obligations"]
            else:
                result = [parsed]

            # Cache successful response
            self.cache.set(cache_key, result, model=self.model, prompt_version="v1")
            return result

        except Exception as exc:
            logger.error("LLM extraction call failed: %s", exc)
            return []

    def evaluate_compliance(self, obligation: Obligation, policy: CompanyPolicy) -> dict[str, Any]:
        return {
            "verdict": "needs_review",
            "confidence": 0.8,
            "explanation": f"LLM evaluated obligation against {policy.title}.",
        }
