"""Governance Reconstruction Receipt (GRR) — institutional memory for one judgment cycle."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from src.crk1.governance_receipt_header import RUNTIME_VERSION, crk1_uuid
from src.crk1.schema_validator import CRK1SchemaValidator


class EvidenceRef(BaseModel):
    ref_id: str
    label: str = ""


class FeatureRef(BaseModel):
    ref_id: str
    description: str = ""


class Hypothesis(BaseModel):
    hypothesis_id: str
    statement: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ValueDimension(BaseModel):
    value_id: str
    label: str = ""
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class Tradeoff(BaseModel):
    raised: str
    lowered: str
    rationale: str


class RejectedAction(BaseModel):
    action: str
    reason: str


class ModelUpdate(BaseModel):
    from_hypothesis: str
    to_hypothesis: str


class ValueUpdate(BaseModel):
    from_value: str
    to_value: str
    rationale: str = ""


class InvariantUpdate(BaseModel):
    invariant_id: str
    change: str


class GRRObservation(BaseModel):
    raw_signals: list[EvidenceRef] = Field(default_factory=list)
    salient_features: list[FeatureRef] = Field(default_factory=list)


class GRRInterpretation(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    selected_model: str = ""


class GRRValuation(BaseModel):
    values_in_play: list[ValueDimension] = Field(default_factory=list)
    tradeoffs: list[Tradeoff] = Field(default_factory=list)


class GRRCommitment(BaseModel):
    chosen_action: str = ""
    rejected_actions: list[RejectedAction] = Field(default_factory=list)


class GRROutcome(BaseModel):
    observed_effects: dict[str, Any] = Field(default_factory=dict)
    unexpected_effects: list[str] = Field(default_factory=list)


class GRRReflection(BaseModel):
    update_to_models: list[ModelUpdate] = Field(default_factory=list)
    update_to_values: list[ValueUpdate] = Field(default_factory=list)
    update_to_invariants: list[InvariantUpdate] = Field(default_factory=list)


class GRRBinding(BaseModel):
    governance_receipt_ids: list[str] = Field(default_factory=list)
    decisive_invariants: list[str] = Field(default_factory=list)
    failure_class_ids: list[str] = Field(default_factory=list)


class GovernanceReconstructionReceipt(BaseModel):
    """
    One judgment cycle — reconstructs what reality looked like, what was believed,
    valued, traded off, and how that fed back into the constitution.
    """

    receipt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generation: int = 0
    cycle: int = 0
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    observation: GRRObservation = Field(default_factory=GRRObservation)
    interpretation: GRRInterpretation = Field(default_factory=GRRInterpretation)
    valuation: GRRValuation = Field(default_factory=GRRValuation)
    commitment: GRRCommitment = Field(default_factory=GRRCommitment)
    outcome: GRROutcome = Field(default_factory=GRROutcome)
    reflection: GRRReflection = Field(default_factory=GRRReflection)
    binding: GRRBinding = Field(default_factory=GRRBinding)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def content_hash(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    @property
    def runtime_version(self) -> str:
        return RUNTIME_VERSION


def build_governance_reconstruction_receipt(
    *,
    generation: int,
    cycle: int,
    observation: GRRObservation,
    interpretation: GRRInterpretation,
    valuation: GRRValuation,
    commitment: GRRCommitment,
    outcome: GRROutcome,
    reflection: GRRReflection,
    binding: GRRBinding,
    receipt_id: str | None = None,
    validate: bool = True,
) -> GovernanceReconstructionReceipt:
    receipt = GovernanceReconstructionReceipt(
        receipt_id=receipt_id or str(uuid.uuid4()),
        generation=generation,
        cycle=cycle,
        observation=observation,
        interpretation=interpretation,
        valuation=valuation,
        commitment=commitment,
        outcome=outcome,
        reflection=reflection,
        binding=binding,
    )
    if validate:
        CRK1SchemaValidator().validate("GovernanceReconstructionReceipt", receipt.to_dict())
    return receipt


def issue_governance_reconstruction_receipt(
    *,
    linked_governance_receipts: list[str],
    epoch: int,
    actor_identity: str,
    context: dict[str, Any],
    observation: dict[str, Any],
    interpretation: dict[str, Any],
    valuation: dict[str, Any],
    commitment: dict[str, Any],
    outcome: dict[str, Any],
    signatures: dict[str, str] | None = None,
    reflection: dict[str, Any] | None = None,
    grr_id: str | None = None,
    timestamp: str | None = None,
    validate: bool = True,
) -> GovernanceReconstructionReceipt:
    """Mint a GRR from loose dict sections (runtime integration path)."""
    _ = signatures  # reserved for future binding extensions
    raw_signals = [
        EvidenceRef(ref_id=str(item), label="")
        for item in observation.get("evidence_refs", [])
    ]
    if not raw_signals and observation.get("raw_signals"):
        raw_signals = [EvidenceRef.model_validate(item) for item in observation["raw_signals"]]

    hypotheses = []
    for item in interpretation.get("hypotheses", []):
        hypotheses.append(
            Hypothesis(
                hypothesis_id=str(item.get("hypothesis_id", item.get("id", "H0"))),
                statement=str(item.get("statement", item.get("description", ""))),
                confidence=float(item.get("confidence", 0.5)),
            )
        )
    selected = str(
        interpretation.get("selected_model")
        or interpretation.get("selected_hypothesis_id")
        or (hypotheses[0].hypothesis_id if hypotheses else "")
    )

    values = []
    for item in valuation.get("values_in_play", []):
        values.append(
            ValueDimension(
                value_id=str(item.get("value_id", item.get("id", "V0"))),
                label=str(item.get("label", item.get("dimension", ""))),
                weight=float(item.get("weight", item.get("priority", 1.0))),
            )
        )

    receipt = GovernanceReconstructionReceipt(
        receipt_id=grr_id or str(uuid.uuid4()),
        generation=int(epoch),
        cycle=int(context.get("cycle", 0)),
        timestamp=timestamp or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        observation=GRRObservation(
            raw_signals=raw_signals,
            salient_features=[
                FeatureRef(ref_id="context", description=json.dumps(context, sort_keys=True))
            ],
        ),
        interpretation=GRRInterpretation(hypotheses=hypotheses, selected_model=selected),
        valuation=GRRValuation(values_in_play=values),
        commitment=GRRCommitment(chosen_action=str(commitment.get("chosen_action", ""))),
        outcome=GRROutcome(observed_effects=dict(outcome)),
        reflection=GRRReflection(
            update_to_invariants=[
                InvariantUpdate(invariant_id=key, change=str(value))
                for key, value in (reflection or {}).get("update_to_invariants", {}).items()
                if isinstance(reflection, dict)
            ]
        ),
        binding=GRRBinding(
            governance_receipt_ids=[crk1_uuid(item) for item in linked_governance_receipts],
            decisive_invariants=list((reflection or {}).get("decisive_invariants", []))
            if isinstance(reflection, dict)
            else [],
        ),
    )
    if validate:
        CRK1SchemaValidator().validate("GovernanceReconstructionReceipt", receipt.to_dict())
    return receipt
