"""Deterministic invariant reconstruction plans (dry-run)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import hashlib
import json
from typing import Any, Literal


ClaimLabel = Literal["asserted", "proven", "rejected"]


@dataclass(slots=True)
class ReconstructionStep:
    step_id: str
    invariant_id: str
    action: str
    rationale: str


@dataclass(slots=True)
class ReconstructionPlan:
    plan_version: str
    case_id: str
    generated_at_utc: str
    deterministic_seed: str
    claim_label: ClaimLabel
    safety_state: str
    rollback_token: str
    steps: list[ReconstructionStep] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_reconstruction_plan(
    *,
    case_id: str,
    drifts: list[dict[str, Any]],
) -> ReconstructionPlan:
    generated_at = datetime.now(UTC).isoformat()
    seed = _hash_text(
        json.dumps(
            {"case_id": case_id, "drifts": drifts, "generated_at_utc": generated_at},
            sort_keys=True,
        )
    )
    steps: list[ReconstructionStep] = []
    for index, drift in enumerate(drifts):
        inv = str(drift.get("invariant_id") or "unknown")
        steps.append(
            ReconstructionStep(
                step_id=f"step-{index + 1:03d}",
                invariant_id=inv,
                action="restore_invariant_dry_run",
                rationale=str(drift.get("drift_summary") or ""),
            )
        )
    if not steps:
        steps.append(
            ReconstructionStep(
                step_id="step-001",
                invariant_id="none",
                action="observe_only",
                rationale="no drift detected",
            )
        )
    claim: ClaimLabel = "proven" if drifts else "asserted"
    return ReconstructionPlan(
        plan_version="scorpion.reconstruction.v1",
        case_id=case_id,
        generated_at_utc=generated_at,
        deterministic_seed=seed,
        claim_label=claim,
        safety_state="dry_run_only",
        rollback_token=f"rollback-{seed[:12]}",
        steps=steps,
        notes=["apply mode blocked in stage 1-2"],
    )
