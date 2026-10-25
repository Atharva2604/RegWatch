"""Declarative Source Adapter driven purely by YAML configuration."""

import logging
from collections.abc import Iterator
from typing import Any
from regwatch.domain.models import LegalType, ListingItem
from regwatch.domain.ports import Fetcher
from regwatch.infrastructure.sources.base import BaseAdapter, ListingDefinition
from regwatch.infrastructure.sources.parsers.html_table import parse_html_table

logger = logging.getLogger(__name__)


class DeclarativeAdapter(BaseAdapter):
    """Adapter whose behavior is fully specified by a YAML configuration file."""

    def __init__(self, fetcher: Fetcher, config: dict[str, Any]) -> None:
        super().__init__(fetcher, config)
        self.key = config.get("key", "unknown")
        self.name = config.get("name", self.key)
        self.jurisdiction = config.get("jurisdiction", "IN")
        self.base_url = config.get("base_url", "https://www.sebi.gov.in")
        self._listings = self._parse_listing_definitions()

    def _parse_listing_definitions(self) -> list[ListingDefinition]:
        defs: list[ListingDefinition] = []
        for raw in self.config.get("listings", []):
            try:
                l_type = LegalType(raw.get("legal_type", "circular"))
            except ValueError:
                l_type = LegalType.OTHER

            defs.append(ListingDefinition(
                name=raw.get("name", "default"),
                legal_type=l_type,
                url=raw["url"],
                parser_type=raw.get("parser", "html_table"),
                selectors=raw.get("selectors"),
                max_pages=raw.get("max_pages", 1),
            ))
        return defs

    def listings(self) -> list[ListingDefinition]:
        return self._listings

    def iter_items(self, listing: ListingDefinition, max_pages: int = 1) -> Iterator[ListingItem]:
        logger.info("Iterating listing '%s' for regulator '%s' (max_pages=%d)", listing.name, self.key, max_pages)

        for page_num in range(1, max_pages + 1):
            try:
                html = self.fetcher.fetch_paged_listing(listing.url, page_num)
            except Exception as exc:
                logger.error("Failed to fetch page %d for listing '%s': %s", page_num, listing.name, exc)
                break

            if not html:
                break

            if listing.parser_type == "html_table":
                items = list(parse_html_table(
                    html=html,
                    source_key=self.key,
                    legal_type=listing.legal_type,
                    base_url=self.base_url,
                ))
                if not items:
                    logger.info("No items found on page %d for listing '%s'. Stopping pagination.", page_num, listing.name)
                    break

                for item in items:
                    yield item
            else:
                logger.warning("Unsupported parser type: %s", listing.parser_type)
                break
