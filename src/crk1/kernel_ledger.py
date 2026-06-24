"""CRK-1 Kernel Ledger — genesis constitutional adoption record."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

KERNEL_LEDGER_GENESIS_ENTRY_ID = "CRK1-KERNEL-LEDGER-0000"
KERNEL_LEDGER_VERSION = "1.0"

TRANSMISSION_LAYER = (
    "K0 — Consequence Transmission",
    "K1 — Immutable Exposure Constraint",
    "K2 — Judgment–Consequence Coupling",
)

PRESERVATION_LAYER = (
    "K3 — Anti‑Insulation Proof",
    "K4 — Consequence Preservation Law",
    "K5 — Mutation Admissibility Test",
    "K6 — Constitutional Drift Envelope",
)

ASSIMILATION_LAYER = (
    "K7 — Interpretive Pluralism Invariant",
    "K8 — Prediction‑Bound Interpretation Law",
    "K9 — Anti‑Monoculture Constraint",
    "K10 — Adversarial Reconstruction Principle",
    "K11 — Interpretive Drift Envelope",
    "K12 — Semantic Exposure Metric (SE(S))",
)

CONTINUITY_GUARANTEES = (
    "Consequences reach judgment.",
    "Consequences cannot be blocked.",
    "Consequences cannot be neutralized by interpretation.",
)


class KernelSpecification(BaseModel):
    transmission_layer: tuple[str, ...] = Field(default=TRANSMISSION_LAYER)
    preservation_layer: tuple[str, ...] = Field(default=PRESERVATION_LAYER)
    assimilation_layer: tuple[str, ...] = Field(default=ASSIMILATION_LAYER)


class ReplayEvidenceAnchor(BaseModel):
    id: str = "E0"
    source_type: Literal["reality"] = "reality"
    admissible: bool = True


class ReplayDecisionAnchor(BaseModel):
    id: str = "D0"
    identity: str = "Root"
    evidence: list[str] = Field(default_factory=lambda: ["E0"])


class ReplayOutcomeAnchor(BaseModel):
    id: str = "O0"
    replayable: bool = True


class ReplayEvidenceFromOutcomeAnchor(BaseModel):
    id: str = "E1"
    replay_of: str = "O0"


class ReplayAnchors(BaseModel):
    evidence_e0: ReplayEvidenceAnchor = Field(default_factory=ReplayEvidenceAnchor)
    decision_d0: ReplayDecisionAnchor = Field(default_factory=ReplayDecisionAnchor)
    outcome_o0: ReplayOutcomeAnchor = Field(default_factory=ReplayOutcomeAnchor)
    evidence_e1: ReplayEvidenceFromOutcomeAnchor = Field(default_factory=ReplayEvidenceFromOutcomeAnchor)


class CRK1KernelLedgerEntry(BaseModel):
    """Immutable first ledger entry — root of trust for CRK-1."""

    entry_id: str = KERNEL_LEDGER_GENESIS_ENTRY_ID
    version: str = KERNEL_LEDGER_VERSION
    entry_type: Literal["Constitutional Adoption Record"] = "Constitutional Adoption Record"
    timestamp: str
    recorded_by: str = "Identity(Root)"
    parent: None = None
    kernel_specification: KernelSpecification = Field(default_factory=KernelSpecification)
    continuity_guarantees: tuple[str, ...] = Field(default=CONTINUITY_GUARANTEES)
    replay_anchors: ReplayAnchors = Field(default_factory=ReplayAnchors)
    signature: str

    def entry_hash(self) -> str:
        payload = self.model_dump(mode="json", exclude={"signature"})
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_canonical_text(self) -> str:
        """Human-readable canonical form stored as the genesis block."""
        spec = self.kernel_specification
        anchors = self.replay_anchors
        lines = [
            "CRK‑1 Kernel Ledger Entry",
            f"Version: {self.version}",
            f"Entry Type: {self.entry_type}",
            f"Timestamp: {self.timestamp}",
            f"Recorded By: {self.recorded_by}",
            f"Parent: {self.parent}",
            "",
            "Kernel Specification:",
            "  Transmission Layer:",
        ]
        for item in spec.transmission_layer:
            lines.append(f"    {item}")
        lines.append("")
        lines.append("  Preservation Layer:")
        for item in spec.preservation_layer:
            lines.append(f"    {item}")
        lines.append("")
        lines.append("  Assimilation Layer:")
        for item in spec.assimilation_layer:
            lines.append(f"    {item}")
        lines.append("")
        lines.append("Continuity Guarantees:")
        for guarantee in self.continuity_guarantees:
            lines.append(f"  - {guarantee}")
        lines.append("")
        lines.append("Replay Anchors:")
        lines.append(
            f'  Evidence({anchors.evidence_e0.id}): source_type = "{anchors.evidence_e0.source_type}", '
            f"admissible = {str(anchors.evidence_e0.admissible).lower()}"
        )
        lines.append(
            f"  Decision({anchors.decision_d0.id}): identity = {anchors.decision_d0.identity}, "
            f"evidence = {anchors.decision_d0.evidence}"
        )
        lines.append(
            f"  Outcome({anchors.outcome_o0.id}): replayable = {str(anchors.outcome_o0.replayable).lower()}"
        )
        lines.append(f"  Evidence({anchors.evidence_e1.id}): replay({anchors.evidence_e1.replay_of})")
        lines.append("")
        lines.append("Signature:")
        lines.append(f"  {self.signature}")
        return "\n".join(lines)


def _now_genesis_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compute_root_signature(entry_id: str, timestamp: str, *, secret: str = "ROOT") -> str:
    body = f"{secret}:{entry_id}:{timestamp}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def create_genesis_kernel_ledger_entry(
    *,
    timestamp: str | None = None,
    root_signature: str | None = None,
) -> CRK1KernelLedgerEntry:
    """Build the canonical genesis adoption record."""
    ts = timestamp or _now_genesis_timestamp()
    signature = root_signature or compute_root_signature(KERNEL_LEDGER_GENESIS_ENTRY_ID, ts)
    return CRK1KernelLedgerEntry(timestamp=ts, signature=signature)


def bootstrap_kernel_ledger_entry(runtime: Any) -> CRK1KernelLedgerEntry:
    """
    Materialize replay anchors on a live CRK-1 runtime and return the genesis ledger entry.

    Establishes E0 → D0 → O0 → replay → E1 on the facade.
    """
    from src.crk1.runtime_facade import CRK1Runtime

    if not isinstance(runtime, CRK1Runtime):
        raise TypeError("runtime must be CRK1Runtime")

    root_id = runtime.kernel.ledgers.identity.id
    evidence = runtime.create_evidence()
    decision = runtime.propose_and_execute(identity=root_id, evidence=[evidence.id])
    outcomes = runtime.get_outcomes(decision.id)
    if not outcomes:
        raise RuntimeError("Genesis bootstrap failed: no outcome from D0")
    outcome = outcomes[0]
    replay_evidence = runtime.replay_outcome(outcome.id)

    entry = create_genesis_kernel_ledger_entry()
    entry.replay_anchors.evidence_e0.id = evidence.id
    entry.replay_anchors.decision_d0.identity = "Root"
    entry.replay_anchors.decision_d0.evidence = [evidence.id]
    entry.replay_anchors.outcome_o0.id = outcome.id
    entry.replay_anchors.evidence_e1.id = replay_evidence.id
    entry.replay_anchors.evidence_e1.replay_of = outcome.id
    return entry
