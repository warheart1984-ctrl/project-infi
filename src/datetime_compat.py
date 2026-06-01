"""Python 3.10-compatible UTC export."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

try:
    from datetime import UTC
except ImportError:  # pragma: no cover - Python 3.10
    UTC = timezone.utc

__all__ = ["UTC", "datetime", "timedelta", "timezone"]
