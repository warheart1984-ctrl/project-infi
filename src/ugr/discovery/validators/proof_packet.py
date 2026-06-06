"""Proof packet contribution validator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidityResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    proof: dict[str, Any] = field(default_factory=dict)


def validate_proof_contribution(
    payload: dict[str, Any],
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
) -> ValidityResult:
    result = ValidityResult(valid=False)
    proof_path = str(payload.get("proof_path") or "").strip()
    gene = str(payload.get("gene") or "").strip()
    if not proof_path and not gene:
        result.errors.append("proof_path or gene is required")
        return result
    if proof_path:
        path = Path(proof_path)
        if not path.is_absolute():
            root = Path(__file__).resolve().parents[4]
            path = root / proof_path
        if not path.exists():
            result.errors.append(f"proof packet not found: {proof_path}")
            return result
    claim_label = str(payload.get("claim_label") or "asserted").strip().lower()
    if claim_label not in {"asserted", "proven", "rejected"}:
        result.errors.append(f"invalid claim_label: {claim_label}")
        return result
    result.invariants.append({"family": "repo_proof_law", "status": "pass", "details": claim_label})
    result.proof = {
        "proof_path": proof_path,
        "gene": gene,
        "claim_label": claim_label,
        "law_id": "REPO_PROOF_LAW",
    }
    result.valid = True
    return result
