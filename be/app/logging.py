"""structlog setup. Logs are JSON and must never carry emails, tokens, photos or meal text.

Only log ids, counts, status codes and route templates. Bodies are never logged.
"""

from __future__ import annotations

import logging

import structlog


def configure_logging(level: str = "INFO") -> None:
    numeric = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
