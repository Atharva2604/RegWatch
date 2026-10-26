"""Shared test fixtures for RegWatch."""
import sys
from pathlib import Path
import pytest

# Ensure repository root is on sys.path for test discovery
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from regwatch.bootstrap import AppContainer, build_test_container


@pytest.fixture
def test_container() -> AppContainer:
    """Return an isolated test container with in-memory repos, fake LLM, and mock queue."""
    return build_test_container()
