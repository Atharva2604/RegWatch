"""Tests for the read-only dashboard data helpers (no network access)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard import data


def test_fmt_dt_converts_utc_to_ist():
    assert data.fmt_dt("2026-10-24T07:04:17.155632+00:00") == "24 Oct 2026, 12:34 IST"


def test_qs_builds_filter_links_and_skips_empty_values():
    assert data.qs({"q": "credit", "type": "circular"}, page=2) == "q=credit&type=circular&page=2"
    assert data.qs({"q": "", "type": "circular", "page": 3}) == "type=circular&page=3"
    assert data.qs(None, verdict="non_compliant") == "verdict=non_compliant"


def test_text_diff_reports_changed_lines():
    diff = data.text_diff("alpha\nbeta\ngamma", "alpha\nBETA\ngamma")
    assert diff is not None
    assert diff["added"] == 1
    assert diff["removed"] == 1
    assert any(line.startswith("+BETA") for line in diff["lines"])


def test_text_diff_needs_two_texts():
    assert data.text_diff("", "text") is None
    assert data.text_diff(None, "text") is None


def test_regulator_for_uses_known_hosts():
    assert data.regulator_for("https://www.sebi.gov.in/legal/circulars/x.html") == "SEBI"
    assert data.regulator_for("https://example.com/a") == "example.com"


def test_sanitize_search_strips_or_filter_syntax():
    cleaned = data.sanitize_search("a,b(c)%")
    assert "," not in cleaned
    assert "(" not in cleaned
    assert data.sanitize_search("  credit   risk  ") == "credit risk"


def test_confidence_is_formatted_as_stored_percentage():
    assert data.fmt_conf("0.85") == "85%"
    assert data.fmt_conf(None) == "—"
