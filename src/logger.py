"""Logging configuration."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import sys

from src.config import get_config

config = get_config()

_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_STDOUT_FALLBACK = None
_STDERR_FALLBACK = None


def _stream_is_usable(stream) -> bool:
    """Return whether a stdio-like stream can be written safely."""
    if stream is None or not hasattr(stream, "write"):
        return False

    try:
        stream.write("")
        if hasattr(stream, "flush"):
            stream.flush()
    except Exception:
        return False

    return True


def ensure_standard_streams():
    """Provide writable fallback streams when Windows pythonw launches without stdio."""
    global _STDOUT_FALLBACK, _STDERR_FALLBACK

    if not _stream_is_usable(sys.stdout):
        _STDOUT_FALLBACK = open(os.devnull, "w", encoding="utf-8")
        sys.stdout = _STDOUT_FALLBACK

    if not _stream_is_usable(sys.stderr):
        _STDERR_FALLBACK = open(os.devnull, "w", encoding="utf-8")
        sys.stderr = _STDERR_FALLBACK


def _configure_handler(handler: logging.Handler):
    """Apply the shared formatter to a handler."""
    handler.setFormatter(logging.Formatter(_FORMAT))
    return handler


def get_logger(name):
    """Get a configured logger without duplicating handlers."""
    ensure_standard_streams()
    logger = logging.getLogger(name)

    if getattr(logger, "_aais_configured", False):
        return logger

    logger.setLevel(config.LOG_LEVEL)
    logger.propagate = False

    log_file = os.getenv("AAIS_LOG_FILE", "").strip()
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.addHandler(
            _configure_handler(logging.FileHandler(log_path, encoding="utf-8"))
        )

    if _stream_is_usable(sys.stderr):
        logger.addHandler(_configure_handler(logging.StreamHandler()))

    if not logger.handlers:
        logger.addHandler(_configure_handler(logging.NullHandler()))

    logger._aais_configured = True
    return logger
