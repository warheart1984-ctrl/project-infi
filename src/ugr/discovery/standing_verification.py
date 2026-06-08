"""Collect verification signals for Library Standing promotion to proven."""

from __future__ import annotations

from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def _repo_relative(path: str | Path) -> Path:
    p = Path(str(path))
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def build_verification_context(
    document: dict[str, Any],
    *,
    manifest_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge manifest verification block and document hints into promotion context."""
    ctx: dict[str, Any] = {}
    source = dict(manifest_entry or document or {})
    verification = dict(source.get("verification") or document.get("verification") or {})
    for key, value in verification.items():
        ctx[key] = value
    artifacts = list(verification.get("artifacts") or document.get("verification_artifacts") or [])
    if artifacts:
        ctx["verification_artifacts"] = artifacts
    if source.get("receipt_verified") is not None:
        ctx["receipt_verified"] = bool(source.get("receipt_verified"))
    if document.get("receipt_verified") is not None:
        ctx["receipt_verified"] = bool(document.get("receipt_verified"))
    for signal in (
        "ci_structural_test",
        "subsystem_genome_gate",
        "workflow_otem_gate",
    ):
        if signal in verification:
            ctx[signal] = bool(verification[signal])
        if signal in document:
            ctx[signal] = bool(document[signal])
    return ctx


def probe_document_verification(document: dict[str, Any]) -> dict[str, Any]:
    """Best-effort local probes for structural tests and gate artifacts."""
    ctx = build_verification_context(document)
    proof_path = str(document.get("proof_path") or "").strip()
    if proof_path:
        packet = _repo_relative(proof_path)
        if packet.exists():
            ctx.setdefault("receipt_verified", True)
    verification = dict(document.get("verification") or {})
    for artifact in verification.get("artifacts") or []:
        rel = str(artifact).strip()
        if rel and _repo_relative(rel).exists():
            ctx.setdefault("verification_artifacts", verification.get("artifacts"))
            if "ci_structural_test" not in ctx:
                lowered = rel.lower()
                if "test" in lowered or "structural" in lowered:
                    ctx["ci_structural_test"] = True
            break
    genome_path = str(document.get("genome_path") or verification.get("genome_path") or "").strip()
    if genome_path and _repo_relative(genome_path).exists():
        ctx.setdefault("subsystem_genome_gate", True)
    workflow_path = str(document.get("workflow_path") or verification.get("workflow_path") or "").strip()
    if workflow_path and _repo_relative(workflow_path).exists():
        ctx.setdefault("workflow_otem_gate", True)
    return ctx


def probe_contribution_verification(receipt: dict[str, Any]) -> dict[str, Any]:
    """Verification context for subsystem/workflow/organ receipts."""
    payload = dict(receipt.get("payload") or {})
    ctx = build_verification_context(payload, manifest_entry=payload)
    invariants = receipt.get("invariants_passed") or []
    for inv in invariants:
        name = str(inv.get("name") or inv.get("invariant") or "").strip().lower()
        status = str(inv.get("status") or "").strip().lower()
        if status != "pass":
            continue
        if "genome" in name or "subsystem" in name:
            ctx["subsystem_genome_gate"] = True
        if "workflow" in name or "otem" in name:
            ctx["workflow_otem_gate"] = True
        if "structural" in name or "ci" in name:
            ctx["ci_structural_test"] = True
    if invariants and all(str(i.get("status") or "").lower() == "pass" for i in invariants):
        ctx.setdefault("receipt_verified", True)
    return ctx
