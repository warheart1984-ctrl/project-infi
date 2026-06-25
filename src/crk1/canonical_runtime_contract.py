"""Canonical Runtime Contract (CRC) v0.1 — behavioral invariants and proof hooks."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from src.crk1.schema_validator import CRK1SchemaValidator

CRC_VERSION = "0.1"
CRC_INVARIANT_IDS: tuple[str, ...] = (
    "CRC-1",
    "CRC-2",
    "CRC-3",
    "CRC-4",
    "CRC-5",
    "CRC-6",
    "CRC-7",
)

CRC_INVARIANT_DESCRIPTIONS: dict[str, str] = {
    "CRC-1": "Reconstruction Primacy — every cycle begins from canonical reconstruction",
    "CRC-2": "Architectural Preservation — canonical decisions immutable; extend only",
    "CRC-3": "Contradiction Detection — contradictions logged before output",
    "CRC-4": "Historical Integrity — append-only institutional memory",
    "CRC-5": "Artifact Production — each cycle yields verifiable artifact",
    "CRC-6": "Invariant Separation — constitutional invariants separate from implementation",
    "CRC-7": "Continuity Improvement — measurable non-negative continuity delta",
}

ArtifactType = Literal["spec", "code", "proof", "trace"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(payload: str | bytes | dict[str, Any]) -> str:
    if isinstance(payload, dict):
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    elif isinstance(payload, str):
        body = payload.encode("utf-8")
    else:
        body = payload
    return hashlib.sha256(body).hexdigest()


def merkle_crc_ids(crc_ids: list[str]) -> str:
    """P2: Merkle root over sorted CRC invariant IDs."""
    ordered = sorted(set(crc_ids))
    if not ordered:
        return sha256_hex("")
    leaves = [sha256_hex(cid) for cid in ordered]
    while len(leaves) > 1:
        next_level: list[str] = []
        for i in range(0, len(leaves), 2):
            left = leaves[i]
            right = leaves[i + 1] if i + 1 < len(leaves) else left
            next_level.append(sha256_hex(left + right))
        leaves = next_level
    return leaves[0]


@dataclass(frozen=True)
class ProofHooks:
    """CRC v0.1 proof hooks P1–P4."""

    proof_recon: str
    proof_invariant: str
    proof_artifact: str
    proof_continuity: str

    def to_dict(self) -> dict[str, str]:
        return {
            "proof_recon": self.proof_recon,
            "proof_invariant": self.proof_invariant,
            "proof_artifact": self.proof_artifact,
            "proof_continuity": self.proof_continuity,
        }

    def composite_receipt(self) -> str:
        return sha256_hex(self.to_dict())


def compute_proof_hooks(
    *,
    reconstruction_source: str,
    invariants_checked: list[str],
    artifact_produced: dict[str, str],
    continuity_score: float,
    prior_continuity_score: float | None,
) -> ProofHooks:
    proof_recon = sha256_hex(reconstruction_source)
    proof_invariant = merkle_crc_ids(invariants_checked)
    proof_artifact = sha256_hex(artifact_produced)
    if prior_continuity_score is None:
        delta = 0.0
    else:
        delta = continuity_score - prior_continuity_score
    proof_continuity = sha256_hex(
        {
            "continuity_score": continuity_score,
            "prior_continuity_score": prior_continuity_score,
            "delta": delta,
            "non_negative": delta >= 0,
        }
    )
    return ProofHooks(
        proof_recon=proof_recon,
        proof_invariant=proof_invariant,
        proof_artifact=proof_artifact,
        proof_continuity=proof_continuity,
    )


@dataclass
class CanonicalTraceObject:
    """CRC v0.1 behavioral ledger entry."""

    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=_now_iso)
    reconstruction_source: str = ""
    contradictions_detected: list[str] = field(default_factory=list)
    invariants_checked: list[str] = field(default_factory=lambda: list(CRC_INVARIANT_IDS))
    artifact_produced: dict[str, str] = field(default_factory=dict)
    memory_update: dict[str, Any] = field(default_factory=lambda: {"append_only": True, "delta": {}})
    continuity_score: float = 0.0
    proof_receipt: str = ""
    proof_hooks: ProofHooks | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "cycle_id": self.cycle_id,
            "timestamp": self.timestamp,
            "reconstruction_source": self.reconstruction_source,
            "contradictions_detected": list(self.contradictions_detected),
            "invariants_checked": list(self.invariants_checked),
            "artifact_produced": dict(self.artifact_produced),
            "memory_update": dict(self.memory_update),
            "continuity_score": self.continuity_score,
            "proof_receipt": self.proof_receipt,
        }
        if self.proof_hooks is not None:
            payload["proof_hooks"] = self.proof_hooks.to_dict()
        return payload


@dataclass
class CRCInvariantViolation:
    invariant_id: str
    message: str


@dataclass
class CRCCycleContext:
    """Inputs for one governed runtime cycle."""

    project_state_hash: str
    contradictions: list[str]
    artifact_type: ArtifactType
    artifact_body: dict[str, Any] | str
    memory_delta: dict[str, Any]
    continuity_score: float
    prior_continuity_score: float | None = None
    reconstruction_completed: bool = True
    architectural_overwrite_attempted: bool = False


class CRCRuntime:
    """CRC v0.1 cycle runner — validates invariants, emits traces, append-only ledger."""

    def __init__(self, *, validator: CRK1SchemaValidator | None = None) -> None:
        self._validator = validator or CRK1SchemaValidator()
        self._ledger: list[CanonicalTraceObject] = []
        self._last_continuity_score: float | None = None

    @property
    def ledger(self) -> list[CanonicalTraceObject]:
        return list(self._ledger)

    def validate_invariants(self, ctx: CRCCycleContext) -> list[CRCInvariantViolation]:
        violations: list[CRCInvariantViolation] = []

        if not ctx.reconstruction_completed or not ctx.project_state_hash:
            violations.append(
                CRCInvariantViolation("CRC-1", "reconstruction must precede reasoning")
            )

        if ctx.architectural_overwrite_attempted:
            violations.append(
                CRCInvariantViolation("CRC-2", "canonical architectural overwrite forbidden")
            )

        if ctx.contradictions and not ctx.reconstruction_completed:
            violations.append(
                CRCInvariantViolation("CRC-3", "contradictions require reconstruction context")
            )

        if ctx.memory_delta and ctx.memory_delta.get("_rewrite_history"):
            violations.append(
                CRCInvariantViolation("CRC-4", "historical rewrite detected in memory delta")
            )

        if not ctx.artifact_body:
            violations.append(
                CRCInvariantViolation("CRC-5", "cycle must produce verifiable artifact")
            )

        if any(str(key).startswith("invariant_") for key in ctx.memory_delta):
            violations.append(
                CRCInvariantViolation(
                    "CRC-6",
                    "invariants must not be stored in mutable memory delta",
                )
            )

        prior = ctx.prior_continuity_score if ctx.prior_continuity_score is not None else self._last_continuity_score
        if prior is not None and ctx.continuity_score < prior:
            violations.append(
                CRCInvariantViolation(
                    "CRC-7",
                    f"continuity regression: {ctx.continuity_score} < {prior}",
                )
            )

        return violations

    def run_cycle(self, ctx: CRCCycleContext) -> CanonicalTraceObject:
        violations = self.validate_invariants(ctx)
        if violations:
            ids = ", ".join(v.invariant_id for v in violations)
            raise ValueError(f"CRC invariant failure: {ids}")

        artifact_hash = sha256_hex(ctx.artifact_body)
        artifact_produced = {"type": ctx.artifact_type, "hash": artifact_hash}
        memory_update = {"append_only": True, "delta": dict(ctx.memory_delta)}
        prior = (
            ctx.prior_continuity_score
            if ctx.prior_continuity_score is not None
            else self._last_continuity_score
        )

        hooks = compute_proof_hooks(
            reconstruction_source=ctx.project_state_hash,
            invariants_checked=list(CRC_INVARIANT_IDS),
            artifact_produced=artifact_produced,
            continuity_score=ctx.continuity_score,
            prior_continuity_score=prior,
        )

        trace = CanonicalTraceObject(
            reconstruction_source=ctx.project_state_hash,
            contradictions_detected=list(ctx.contradictions),
            invariants_checked=list(CRC_INVARIANT_IDS),
            artifact_produced=artifact_produced,
            memory_update=memory_update,
            continuity_score=ctx.continuity_score,
            proof_receipt=hooks.composite_receipt(),
            proof_hooks=hooks,
        )

        self._validator.validate("CanonicalTraceObject", trace.to_dict())
        self._ledger.append(trace)
        self._last_continuity_score = ctx.continuity_score
        return trace

    def bind_genesis_r0(self, r0_hash: str) -> dict[str, str]:
        """Genesis Protocol → CRC: anchor invariant set to immutable R0."""
        anchor = sha256_hex({"crc_version": CRC_VERSION, "r0_hash": r0_hash, "invariants": list(CRC_INVARIANT_IDS)})
        return {
            "crc_version": CRC_VERSION,
            "r0_anchor": anchor,
            "invariant_set": ",".join(CRC_INVARIANT_IDS),
        }
