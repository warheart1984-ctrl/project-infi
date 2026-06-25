"""CRK-T5 Reference Integrity Layer (RIL) — canonical reference signals and drift guards."""

from src.t5.drift import DriftGuard, DriftCheckResult, DriftDetected
from src.t5.invariants import (
    DriftAlert,
    DriftAlertThreshold,
    InvariantLedger,
    InvariantProof,
    InvariantViolation,
)
from src.t5.reference import ReferenceSignal

__all__ = [
    "DriftAlert",
    "DriftAlertThreshold",
    "DriftCheckResult",
    "DriftDetected",
    "DriftGuard",
    "InvariantLedger",
    "InvariantProof",
    "InvariantViolation",
    "ReferenceSignal",
]
