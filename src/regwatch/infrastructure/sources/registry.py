"""Source Adapter Registry and Dynamic Discovery."""

import logging
from pathlib import Path
from typing import Any, Callable, Type
import yaml
from regwatch.domain.ports import Fetcher
from regwatch.infrastructure.sources.base import BaseAdapter
from regwatch.infrastructure.sources.declarative import DeclarativeAdapter

logger = logging.getLogger(__name__)

# Registry maps
_CUSTOM_ADAPTERS: dict[str, Type[BaseAdapter]] = {}
_CONFIG_CACHE: dict[str, dict[str, Any]] = {}


def register_adapter(key: str) -> Callable[[Type[BaseAdapter]], Type[BaseAdapter]]:
    """Decorator to register a custom source adapter class."""
    def decorator(cls: Type[BaseAdapter]) -> Type[BaseAdapter]:
        _CUSTOM_ADAPTERS[key] = cls
        return cls
    return decorator


def load_all_sources(config_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Scan and load all YAML configuration files in the source config directory."""
    if not config_dir:
        config_dir = Path(__file__).parent / "config"

    if not config_dir.exists():
        return {}

    configs: dict[str, dict[str, Any]] = {}
    for yaml_path in config_dir.glob("*.yaml"):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                if cfg and "key" in cfg:
                    configs[cfg["key"]] = cfg
        except Exception as exc:
            logger.error("Failed to parse source YAML at %s: %s", yaml_path, exc)

    _CONFIG_CACHE.update(configs)
    return configs


def get_adapter(source_key: str, fetcher: Fetcher) -> BaseAdapter:
    """Instantiate a source adapter for a given key (custom class or declarative)."""
    # 1. Custom registered class (Level 3)
    if source_key in _CUSTOM_ADAPTERS:
        return _CUSTOM_ADAPTERS[source_key](fetcher)

    # 2. Declarative YAML config (Level 1)
    if not _CONFIG_CACHE:
        load_all_sources()

    cfg = _CONFIG_CACHE.get(source_key)
    if not cfg:
        # Retry with fresh load
        load_all_sources()
        cfg = _CONFIG_CACHE.get(source_key)

    if not cfg:
        raise ValueError(f"No source adapter or YAML configuration registered for key: '{source_key}'")

    return DeclarativeAdapter(fetcher=fetcher, config=cfg)
