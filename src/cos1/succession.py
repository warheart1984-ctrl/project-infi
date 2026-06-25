"""ContinuitySuccession — transferability and RCM-1 continuity state."""

from __future__ import annotations

from src.continuity.stewardability.operating_conditions import (
    StewardabilityConditions,
    is_stewardability_viable,
)
from src.continuity.stewardability.regenerative_model import (
    ContinuityState,
    continuity_succeeded,
    next_continuity_state,
)
from src.cos1.constitutional_bridge import epistemic_conditions_from_snapshot
from src.cos1.memory import ContinuityMemory


class ContinuitySuccession:
    def __init__(self, memory: ContinuityMemory) -> None:
        self._memory = memory
        self._state = ContinuityState(
            artifacts_intact=False,
            stewards_present=False,
            stewardability_viable=False,
        )

    def update(self, conditions: StewardabilityConditions) -> ContinuityState:
        register = self._memory.get_stewardability_register()
        merged = self._merge_epistemic_from_memory(conditions)
        self._state = next_continuity_state(self._state, merged, register)
        self._state = ContinuityState(
            artifacts_intact=self._memory.artifacts_intact(),
            stewards_present=self._state.stewards_present,
            stewardability_viable=self._state.stewardability_viable,
        )
        return self._state

    def _merge_epistemic_from_memory(
        self,
        conditions: StewardabilityConditions,
    ) -> StewardabilityConditions:
        snapshot = self._memory.get_constitutional_snapshot()
        if snapshot is None:
            return conditions
        epistemic_map = epistemic_conditions_from_snapshot(snapshot)
        epistemic = conditions.epistemic.model_copy(
            update={
                "history_accessible": (
                    conditions.epistemic.history_accessible or epistemic_map["history_accessible"]
                ),
                "registers_complete_enough": (
                    conditions.epistemic.registers_complete_enough
                    or epistemic_map["registers_complete_enough"]
                ),
                "failures_visible": (
                    conditions.epistemic.failures_visible or epistemic_map["failures_visible"]
                ),
                "reasoning_transparent": (
                    conditions.epistemic.reasoning_transparent
                    or epistemic_map["reasoning_transparent"]
                ),
            }
        )
        return conditions.model_copy(update={"epistemic": epistemic})

    def get_state(self) -> ContinuityState:
        return self._state

    def continuity_succeeded(self) -> bool:
        return continuity_succeeded(self._state)

    def stewardability_viable(self, conditions: StewardabilityConditions) -> bool:
        return is_stewardability_viable(self._merge_epistemic_from_memory(conditions))
