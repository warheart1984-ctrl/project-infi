"""Environment flags for optional OTEM Temporal worker integration."""

from __future__ import annotations

import os

OTEM_TEMPORAL_ENABLED = os.getenv("AAIS_OTEM_TEMPORAL_ENABLED", "0").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233").strip() or "localhost:7233"
OTEM_TEMPORAL_TASK_QUEUE = (
    os.getenv("AAIS_OTEM_TEMPORAL_TASK_QUEUE", "aais-otem-exec").strip() or "aais-otem-exec"
)
OTEM_TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default").strip() or "default"


def otem_temporal_enabled() -> bool:
    """Return True when Temporal orchestration is requested and SDK is importable."""
    if not OTEM_TEMPORAL_ENABLED:
        return False
    try:
        import temporalio  # noqa: F401
    except ImportError:
        return False
    return True
