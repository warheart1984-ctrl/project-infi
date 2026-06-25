from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from constitutional.core.graph import validate_transition
from constitutional.core.models import Transition


class TransitionLedger(BaseModel):
    entries: List[Transition] = Field(default_factory=list)

    def append(self, t: Transition) -> None:
        validate_transition(t.from_state, t.to_state)
        self.entries.append(t)

    def for_state(self, state_object_id: str) -> List[Transition]:
        return [e for e in self.entries if e.state_object_id == state_object_id]
