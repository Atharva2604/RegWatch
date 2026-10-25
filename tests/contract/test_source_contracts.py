"""Contract test suite for regulatory source adapters."""

import pytest
from regwatch.bootstrap import build_test_container
from regwatch.domain.models import LegalType, ListingItem
from regwatch.infrastructure.sources.parsers.html_table import parse_html_table
from regwatch.infrastructure.sources.registry import get_adapter, load_all_sources


SAMPLE_SEBI_HTML = """
<table>
  <tr>
    <td>Oct 20, 2026</td>
    <td><a href="/legal/circulars/cscrf_guidelines.html">Cyber Security and Resilience Framework (CSCRF)</a></td>
  </tr>
  <tr>
    <td>Sep 15, 2026</td>
    <td><a href="/legal/circulars/kyc_amendment.html">Amendment to KYC norms for stock brokers</a></td>
  </tr>
</table>
"""


def test_html_table_parser_emits_canonical_listing_items() -> None:
    items = list(parse_html_table(
        html=SAMPLE_SEBI_HTML,
        source_key="sebi",
        legal_type=LegalType.CIRCULAR,
    ))
    assert len(items) == 2

    first = items[0]
    assert isinstance(first, ListingItem)
    assert first.source_key == "sebi"
    assert first.title == "Cyber Security and Resilience Framework (CSCRF)"
    assert first.url == "https://www.sebi.gov.in/legal/circulars/cscrf_guidelines.html"
    assert first.legal_type == LegalType.CIRCULAR
    assert first.published_date is not None
    assert first.published_date.year == 2026


def test_registered_sources_satisfy_adapter_contract() -> None:
    container = build_test_container()
    sources = load_all_sources()
    assert "sebi" in sources
    assert "fake_regulator" in sources

    # Test SEBI adapter
    sebi_adapter = get_adapter("sebi", container.fetcher)
    listings = sebi_adapter.listings()
    assert len(listings) >= 3
    assert any(l.name == "circulars" for l in listings)

    # Test FakeRegulator adapter (0-code extensibility)
    fake_adapter = get_adapter("fake_regulator", container.fetcher)
    assert fake_adapter.key == "fake_regulator"
    assert len(fake_adapter.listings()) == 1
