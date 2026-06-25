"""ContinuityRuntime — executes stewardship operations."""

from __future__ import annotations

from src.continuity.stewardability.capacity_test import StewardshipCapacityTestResult
from src.continuity.stewardability.emergence_protocol import (
    EmergenceCandidate,
    EmergenceResult,
    run_steward_emergence_protocol,
)
from src.continuity.stewardability.register import StewardDemonstration
from src.cos1.memory import ContinuityMemory


class ContinuityRuntime:
    def __init__(self, memory: ContinuityMemory) -> None:
        self._memory = memory

    def run_emergence(
        self,
        candidate: EmergenceCandidate,
        demo: StewardDemonstration,
        *,
        capacity_test: StewardshipCapacityTestResult | None = None,
        require_capacity_test: bool = False,
    ) -> EmergenceResult:
        register = self._memory.get_stewardability_register()
        return run_steward_emergence_protocol(
            register,
            candidate,
            demo,
            capacity_test=capacity_test,
            require_capacity_test=require_capacity_test,
        )
