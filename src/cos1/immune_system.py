"""ContinuityImmuneSystem — drift detection across continuity layers."""

from __future__ import annotations

from src.continuity.stewardability.drift_detector import DriftSignal, detect_stewardability_drift
from src.cos1.memory import ContinuityMemory


class ContinuityImmuneSystem:
    def __init__(self, memory: ContinuityMemory) -> None:
        self._memory = memory

    def check_stewardability_drift(self) -> list[DriftSignal]:
        register = self._memory.get_stewardability_register()
        return detect_stewardability_drift(register)
