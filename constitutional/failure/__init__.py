"""Failure register integration — bridge and succession gates."""

from constitutional.failure.bridge import (
    feared_failures_from_register,
    historical_failure_classes_for_layer,
    record_epistemic_failures,
)
from constitutional.failure.governance import succession_failure_continuity_ready

__all__ = [
    "feared_failures_from_register",
    "historical_failure_classes_for_layer",
    "record_epistemic_failures",
    "succession_failure_continuity_ready",
]
