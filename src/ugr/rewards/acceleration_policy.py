"""Acceleration-token policy switches for governed UGR rewards."""

from __future__ import annotations

import os


def acceleration_tokens_enabled() -> bool:
    """Return whether acceleration rewards may affect Cloud Forge routing."""
    return os.getenv("UGR_ACCELERATION_TOKENS_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
