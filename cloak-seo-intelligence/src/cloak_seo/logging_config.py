"""Centralized logging setup."""

from __future__ import annotations

import logging

from config import get_settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure root logging once, using the level from settings."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, ensuring logging is configured first."""
    configure_logging()
    return logging.getLogger(name)
