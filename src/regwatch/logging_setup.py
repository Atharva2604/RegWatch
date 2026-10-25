"""Structured logging setup with correlation context for RegWatch."""

import logging
import sys
from contextvars import ContextVar
from typing import Any

# Context variables for distributed tracing across pipeline stages
_RUN_ID: ContextVar[str] = ContextVar("run_id", default="")
_SOURCE_KEY: ContextVar[str] = ContextVar("source_key", default="")
_JOB_ID: ContextVar[str] = ContextVar("job_id", default="")


def set_log_context(run_id: str = "", source_key: str = "", job_id: str = "") -> None:
    """Set correlation IDs for current execution context."""
    if run_id:
        _RUN_ID.set(run_id)
    if source_key:
        _SOURCE_KEY.set(source_key)
    if job_id:
        _JOB_ID.set(job_id)


class ContextLogFormatter(logging.Formatter):
    """Formats log records including correlation IDs for distributed tracing."""

    def format(self, record: logging.LogRecord) -> str:
        run_id = _RUN_ID.get()
        source = _SOURCE_KEY.get()
        job_id = _JOB_ID.get()

        context_tags = []
        if run_id:
            context_tags.append(f"run={run_id}")
        if source:
            context_tags.append(f"src={source}")
        if job_id:
            context_tags.append(f"job={job_id}")

        tag_str = f" [{', '.join(context_tags)}]" if context_tags else ""
        record.msg = f"{record.msg}{tag_str}"
        return super().format(record)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with unified formatting."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    formatter = ContextLogFormatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if reconfigured
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Convenience helper to retrieve typed module logger."""
    return logging.getLogger(name)
