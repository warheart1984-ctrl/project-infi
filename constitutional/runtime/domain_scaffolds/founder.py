"""Founder runtime — state documents and receipt kinds."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RUNTIME_NAME = "FounderRuntime"

FounderRole = Literal["Architect", "Builder", "Leader", "Operator", "Other"]
RoleSwitchReceiptKind = Literal["EnterRole", "ExitRole", "ForcedSwitch"]
EnergyReceiptKind = Literal["Observation"]
DecisionLoadReceiptKind = Literal["Spike", "Relief"]


class RoleStateDoc(BaseModel):
    state_type: Literal["RoleState"] = "RoleState"
    role_id: str
    role: FounderRole
    active: bool = False
    time_share: float = Field(default=0.0, ge=0.0, le=1.0)


class EnergyStateDoc(BaseModel):
    state_type: Literal["EnergyState"] = "EnergyState"
    snapshot_id: str
    energy_level: float = Field(ge=0.0, le=1.0)
    focus_quality: float = Field(ge=0.0, le=1.0)
    fatigue_signals: list[str] = Field(default_factory=list)


class PriorityStateDoc(BaseModel):
    state_type: Literal["PriorityState"] = "PriorityState"
    priority_id: str
    domain: str
    rank: int = 0
    alignment_with_role: str = ""


class DecisionLoadStateDoc(BaseModel):
    state_type: Literal["DecisionLoadState"] = "DecisionLoadState"
    snapshot_id: str
    decisions_pending: int = 0
    decisions_made: int = 0
    complexity_index: float = Field(default=0.0, ge=0.0)
