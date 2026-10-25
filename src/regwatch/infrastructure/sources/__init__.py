"""Source plugin system: declarative YAML sources, custom adapters, and parser plugins."""

from regwatch.infrastructure.sources.base import BaseAdapter
from regwatch.infrastructure.sources.declarative import DeclarativeAdapter
from regwatch.infrastructure.sources.registry import get_adapter, load_all_sources, register_adapter

__all__ = [
    "BaseAdapter",
    "DeclarativeAdapter",
    "get_adapter",
    "load_all_sources",
    "register_adapter",
]
