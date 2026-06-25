from __future__ import annotations

from typing import Any, Dict

from constitutional.core.graph import validate_transition
from constitutional.core.ledger import TransitionLedger
from constitutional.core.models import StateObject, Transition


class ConstitutionalStateRuntime:
    """In-process constitutional state registry, ledger, reconstruction, and replay."""

    def __init__(self) -> None:
        self._states: Dict[str, StateObject] = {}
        self._ledger = TransitionLedger()

    def register_state(self, state: StateObject) -> None:
        if state.state_id in self._states:
            raise ValueError("State already registered")
        self._states[state.state_id] = state.model_copy(deep=True)

    def get_state(self, state_id: str) -> StateObject:
        if state_id not in self._states:
            raise KeyError(f"unknown state_id: {state_id}")
        return self._states[state_id].model_copy(deep=True)

    def apply_transition(self, t: Transition) -> StateObject:
        validate_transition(t.from_state, t.to_state)
        state = self._states[t.state_object_id]
        state.apply_transition(t)
        self._ledger.append(t)
        return state.model_copy(deep=True)

    def reconstruct_state(self, state_id: str) -> StateObject:
        base = self._states[state_id].model_copy(deep=True)
        base.current_state = "Proposed"
        base.version = 0
        base.history = []
        for t in self._ledger.for_state(state_id):
            base.apply_transition(t)
        return base

    def replay(self, state_id: str) -> Dict[str, Any]:
        canonical = self._states[state_id]
        reconstructed = self.reconstruct_state(state_id)
        diverged = canonical.current_state != reconstructed.current_state
        return {
            "state_id": state_id,
            "canonical_state": canonical.current_state,
            "reconstructed_state": reconstructed.current_state,
            "diverged": diverged,
            "history_length": len(reconstructed.history),
            "canonical_version": canonical.version,
            "reconstructed_version": reconstructed.version,
        }

    @property
    def ledger(self) -> TransitionLedger:
        return self._ledger
