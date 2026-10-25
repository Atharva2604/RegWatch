"""Shared test fixtures for RegWatch."""

import pytest
from regwatch.bootstrap import AppContainer, build_test_container


@pytest.fixture
def test_container() -> AppContainer:
    """Return an isolated test container with in-memory repos, fake LLM, and mock queue."""
    return build_test_container()
