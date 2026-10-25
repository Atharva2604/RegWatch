"""Root CLI entrypoint for RegWatch.

Enables running commands seamlessly via `python cli.py <command>`
without needing explicit PYTHONPATH or pip editable installation.
"""

import sys
from pathlib import Path

# Add src/ directory to sys.path so regwatch package is always discoverable
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from regwatch.interfaces.cli import app

if __name__ == "__main__":
    app()
