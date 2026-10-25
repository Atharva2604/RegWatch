"""Base Source Adapter abstraction (Template Method pattern)."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from regwatch.domain.models import FetchedContent, LegalType, ListingItem
from regwatch.domain.ports import Fetcher


@dataclass(frozen=True)
class ListingDefinition:
    """Configuration for a specific regulatory listing category."""
    name: str
    legal_type: LegalType
    url: str
    parser_type: str = "html_table"
    selectors: dict[str, str] | None = None
    max_pages: int = 1


class BaseAdapter(ABC):
    """Abstract base class for all regulatory source adapters."""

    key: str
    name: str
    jurisdiction: str = "IN"

    def __init__(self, fetcher: Fetcher, config: dict[str, Any] | None = None) -> None:
        self.fetcher = fetcher
        self.config = config or {}

    @abstractmethod
    def listings(self) -> list[ListingDefinition]:
        """Return all listing definitions provided by this regulator."""

    @abstractmethod
    def iter_items(self, listing: ListingDefinition, max_pages: int = 1) -> Iterator[ListingItem]:
        """Yield canonical ListingItems from this listing."""

    def fetch_content(self, item: ListingItem) -> FetchedContent:
        """Fetch content for a listing item using the shared polite fetcher."""
        return self.fetcher.fetch_document_content(item.url)
