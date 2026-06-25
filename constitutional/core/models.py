from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field

StateName = str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Transition(BaseModel):
    transition_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state_object_id: str
    from_state: StateName
    to_state: StateName
    receipt_id: str
    runtime: str
    legal_basis: str
    accountable_party: str
    timestamp: datetime = Field(default_factory=_utc_now)


class StateObject(BaseModel):
    state_id: str
    state_type: str
    version: int = 0
    current_state: StateName = "Proposed"

    invariants: List[str] = Field(default_factory=list)
    evidence_requirements: List[str] = Field(default_factory=list)
    authority_model: List[str] = Field(default_factory=list)
    reproducibility_requirements: List[str] = Field(default_factory=list)
    impact_boundaries: List[str] = Field(default_factory=list)
    accountability_chain: List[str] = Field(default_factory=list)
    vulnerable_to: List[str] = Field(default_factory=list)
    reconstructability_threats: List[str] = Field(default_factory=list)

    history: List[Transition] = Field(default_factory=list)

    def apply_transition(self, t: Transition) -> None:
        if t.state_object_id != self.state_id:
            raise ValueError("Transition state_object_id mismatch")
        if t.from_state != self.current_state:
            raise ValueError(f"Illegal transition: {self.current_state} → {t.to_state}")
        self.current_state = t.to_state
        self.version += 1
        self.history.append(t)
