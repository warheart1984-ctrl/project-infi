"""CEC-1 continuity execution preflight and propagation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ContinuityExecutionCheck:
    ok: bool
    payload: dict[str, Any]
    violations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        row = dict(self.payload)
        row["continuity_ok"] = self.ok
        row["violations"] = list(self.violations)
        return row


def _darz_context(args: dict[str, Any]) -> dict[str, Any]:
    darz = args.get("darz") if isinstance(args, dict) else None
    return dict(darz or {}) if isinstance(darz, dict) else {}


def evaluate_continuity_execution(args: dict[str, Any]) -> ContinuityExecutionCheck | None:
    """Return CEC-1 preflight status for continuity-typed AAES action args."""

    darz = _darz_context(args)
    if not darz:
        return None

    coherence = dict(darz.get("cross_kernel_coherence") or {})
    continuity_proof = dict(darz.get("continuity_proof") or {})
    violations = list(coherence.get("violations") or [])
    if coherence and not bool(coherence.get("continuity_ok", False)):
        violations.append("cec.cross_kernel_coherence_failed")
    if continuity_proof and continuity_proof.get("proof_status") != "PROVEN":
        violations.append("cec.continuity_proof_not_proven")
    if continuity_proof and not bool(continuity_proof.get("replay_stable", False)):
        violations.append("cec.replay_mismatch_detected")
    for required in ("darz_node_id", "substrate_role", "bridge_hash"):
        if not darz.get(required):
            violations.append(f"cec.{required}_missing")

    payload = {
        "darz_node_id": darz.get("darz_node_id"),
        "substrate_role": darz.get("substrate_role"),
        "bridge_hash": darz.get("bridge_hash"),
        "wave_signature": dict(darz.get("wave_signature") or {}),
        "continuity_proof": continuity_proof,
        "cross_kernel_coherence": coherence,
    }
    deduped = tuple(dict.fromkeys(str(item) for item in violations))
    return ContinuityExecutionCheck(ok=not deduped, payload=payload, violations=deduped)


def attach_continuity_execution(
    payload: dict[str, Any],
    check: ContinuityExecutionCheck | None,
) -> dict[str, Any]:
    """Attach CEC-1 propagation fields to an AAES event payload."""

    if check is None:
        return dict(payload)
    wrapped = dict(payload)
    wrapped["continuity_execution"] = check.to_dict()
    return wrapped
