"""Optional Temporal.io orchestration for OTEM execution substrate."""

from src.otem_temporal.config import (
    OTEM_TEMPORAL_TASK_QUEUE,
    TEMPORAL_ADDRESS,
    otem_temporal_enabled,
)

__all__ = [
    "OTEM_TEMPORAL_TASK_QUEUE",
    "TEMPORAL_ADDRESS",
    "otem_temporal_enabled",
]
