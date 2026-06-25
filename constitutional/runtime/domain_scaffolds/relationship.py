"""Relationship runtime — state documents and receipt kinds."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RUNTIME_NAME = "RelationshipRuntime"

RelationshipType = Literal["collaborator", "ally", "mentor", "other"]
TrustDirection = Literal["earned", "lost"]
InteractionReceiptKind = Literal["Contact", "Collaboration", "Conflict", "Repair"]
CommitmentReceiptKind = Literal["Create", "Fulfill", "Miss", "Renegotiate"]
TrustReceiptKind = Literal["TrustEarned", "TrustLost"]


class PersonStateDoc(BaseModel):
    state_type: Literal["PersonState"] = "PersonState"
    person_id: str
    role: str
    importance: str = "normal"
    trust_level: float = Field(default=0.5, ge=0.0, le=1.0)
    last_contact_at: str | None = None


class RelationshipStateDoc(BaseModel):
    state_type: Literal["RelationshipState"] = "RelationshipState"
    relationship_id: str
    person_id: str
    type: RelationshipType = "collaborator"
    depth: str = "shallow"
    trajectory: str = "stable"


class InteractionStateDoc(BaseModel):
    state_type: Literal["InteractionState"] = "InteractionState"
    interaction_id: str
    person_id: str
    date: str
    channel: str
    topics: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)


class CommitmentStateDoc(BaseModel):
    state_type: Literal["CommitmentState"] = "CommitmentState"
    commitment_id: str
    person_id: str
    promise: str
    due_at: str | None = None
    status: str = "open"


class TrustSignalStateDoc(BaseModel):
    state_type: Literal["TrustSignalState"] = "TrustSignalState"
    signal_id: str
    person_id: str
    direction: TrustDirection
    weight: float = Field(default=1.0, ge=0.0)
