"""CRK-1 wire objects v0.1 — common envelope + typed payload/links."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

CRK1_OBJECT_TYPES = (
    "Identity",
    "Decision",
    "Outcome",
    "Evidence",
    "Interpretation",
    "Receipt",
)

ObjectType = Literal["Identity", "Decision", "Outcome", "Evidence", "Interpretation", "Receipt"]

IdentityKind = Literal["Person", "Organization", "System", "Process", "Other"]
DecisionStatus = Literal["Proposed", "Committed", "RolledBack"]
EvidenceKind = Literal["Log", "Metric", "Document", "TestResult", "Other"]
InvariantStatus = Literal["Pass", "Fail", "Skip"]


class CRK1Envelope(BaseModel):
    """Common envelope shared by all CRK-1 v0.1 wire objects."""

    id: str
    type: ObjectType
    created_at: str
    created_by: str
    epoch: int = Field(ge=0)
    receipt_id: str
    payload: dict[str, Any]
    links: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @property
    def label(self) -> str:
        value = self.payload.get("label")
        return str(value) if value is not None else self.type


class IdentityPayload(BaseModel):
    label: str
    kind: IdentityKind
    attributes: dict[str, Any] = Field(default_factory=dict)


class DecisionPayload(BaseModel):
    label: str
    description: str = ""
    scope: str = ""
    status: DecisionStatus


class OutcomePayload(BaseModel):
    label: str
    state_change: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)


class EvidencePayload(BaseModel):
    label: str
    kind: EvidenceKind
    uri: str = ""
    summary: str = ""
    hash: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)


class InterpretationPayload(BaseModel):
    label: str
    statement: str
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
    invariant_checks: list[str] = Field(default_factory=list)


class InvariantResult(BaseModel):
    id: str
    status: InvariantStatus


class ReceiptSignature(BaseModel):
    by: str
    kind: str
    signature: str
    at: str


class ReceiptPayload(BaseModel):
    action_type: str
    object_type: ObjectType
    object_id: str
    kernel_version: str = "K0-K15"
    invariant_results: list[InvariantResult] = Field(default_factory=list)
    drift_snapshot: dict[str, float] = Field(default_factory=dict)
    signatures: list[ReceiptSignature] = Field(default_factory=list)


def parse_crk1_object(data: dict[str, Any]) -> CRK1Envelope:
    return CRK1Envelope.model_validate(data)


def prefab_for_type(object_type: ObjectType) -> str:
    """Unity prefab name for DARZ-VR GraphController."""
    mapping = {
        "Identity": "IdentityNodePrefab",
        "Decision": "DecisionNodePrefab",
        "Outcome": "OutcomeNodePrefab",
        "Evidence": "EvidenceNodePrefab",
        "Interpretation": "InterpretationNodePrefab",
        "Receipt": "ReceiptNodePrefab",
    }
    return mapping[object_type]


def layer_for_type(object_type: ObjectType) -> str:
    """Unity layer name under GraphRoot."""
    mapping = {
        "Identity": "IdentityLayer",
        "Decision": "DecisionLayer",
        "Outcome": "OutcomeLayer",
        "Evidence": "EvidenceLayer",
        "Interpretation": "InterpretationLayer",
        "Receipt": "ReceiptLayer",
    }
    return mapping[object_type]
