"""Target-state workflow and patch plan generation (dry-run)."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from mechanic.common import hash_text, json_stable
from mechanic.rebuild.runtime_profile import build_runtime_profile


@dataclass(slots=True)
class ReconstructionStep:
    step_id: str
    code: str
    action: str
    rationale: str


@dataclass(slots=True)
class ReconstructionPlan:
    plan_version: str
    case_id: str
    generated_at_utc: str
    deterministic_seed: str
    claim_label: str
    safety_state: str
    rollback_token: str
    steps: list[ReconstructionStep] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def build_reconstruction_plan(*, case_id: str, drifts: list[dict[str, Any]]) -> ReconstructionPlan:
    generated_at = datetime.now(UTC).isoformat()
    seed = hash_text(json_stable({"case_id": case_id, "drifts": drifts, "generated_at_utc": generated_at}))
    steps: list[ReconstructionStep] = []
    for index, drift in enumerate(drifts):
        code = str(drift.get("code") or drift.get("invariant_id") or "unknown")
        steps.append(
            ReconstructionStep(
                step_id=f"step-{index + 1:03d}",
                code=code,
                action="restore_invariant_dry_run",
                rationale=str(drift.get("drift_summary") or ""),
            )
        )
    if not steps:
        steps.append(
            ReconstructionStep(
                step_id="step-001",
                code="none",
                action="observe_only",
                rationale="no drift detected",
            )
        )
    claim = "proven" if drifts else "asserted"
    return ReconstructionPlan(
        plan_version="mechanic.reconstruction.v1",
        case_id=case_id,
        generated_at_utc=generated_at,
        deterministic_seed=seed,
        claim_label=claim,
        safety_state="dry_run_only",
        rollback_token=f"rollback-{seed[:12]}",
        steps=steps,
        notes=["apply mode blocked in MVP", "operator must apply patch_plan manually"],
    )


def build_target_workflow(*, genome: dict[str, Any], drifts: list[dict[str, Any]]) -> dict[str, Any]:
    graph = copy.deepcopy(genome)
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    codes = {str(d.get("code")) for d in drifts}
    if "GOV-12" in codes:
        for mc in [n for n in nodes if str(n.get("type")) == "model_call"]:
            exc_id = f"exc:planned:{mc.get('id')}"
            if not any(str(n.get("id")) == exc_id for n in nodes):
                nodes.append(
                    {
                        "id": exc_id,
                        "type": "exception_path",
                        "label": "surfaced_exception",
                        "source_path": mc.get("source_path"),
                        "attrs": {"provisional": True, "source": "mechanic_rebuild"},
                    }
                )
                edges.append(
                    {
                        "source": mc.get("id"),
                        "target": exc_id,
                        "type": "exception_of",
                        "attrs": {},
                    }
                )
    if "HUM-05" in codes or "HUM-03" in codes:
        for wf in [n for n in nodes if str(n.get("type")) == "workflow_automation"]:
            hc_id = f"human:planned:{wf.get('id')}"
            if not any(str(n.get("id")) == hc_id for n in nodes):
                nodes.append(
                    {
                        "id": hc_id,
                        "type": "human_control",
                        "label": "approval_gate",
                        "source_path": wf.get("source_path"),
                        "attrs": {"provisional": True, "source": "mechanic_rebuild"},
                    }
                )
                edges.append(
                    {
                        "source": wf.get("id"),
                        "target": hc_id,
                        "type": "escalates_to_human",
                        "attrs": {},
                    }
                )
    if "RNT-08" in codes:
        for mc in [n for n in nodes if str(n.get("type")) == "model_call"][:1]:
            val_id = f"validate:planned:{mc.get('id')}"
            nodes.append(
                {
                    "id": val_id,
                    "type": "tool_binding",
                    "label": "output_validator",
                    "source_path": "",
                    "attrs": {"allowed_actions": ["validate_output"], "provisional": True},
                }
            )
            edges.append({"source": val_id, "target": mc.get("id"), "type": "validates", "attrs": {}})
    graph["nodes"] = nodes
    graph["edges"] = edges
    graph["metadata"] = dict(graph.get("metadata") or {})
    graph["metadata"]["rebuild"] = True
    return {
        "schema_version": "target_workflow.v1",
        "case_id": graph.get("case_id"),
        "genome_hash": graph.get("genome_hash"),
        "graph": graph,
        "safety_state": "dry_run_only",
        "claim_label": "asserted",
    }


def build_patch_plan(*, case_id: str, drifts: list[dict[str, Any]], genome: dict[str, Any]) -> dict[str, Any]:
    patches: list[dict[str, Any]] = []
    for drift in drifts:
        code = str(drift.get("code") or "")
        evidence = drift.get("evidence") or {}
        path = str(evidence.get("source_path") or "")
        if code == "GOV-12" and path:
            patches.append(
                {
                    "patch_id": f"patch-{code}-{hash_text(path)[:8]}",
                    "code": code,
                    "action": "add_exception_handler_stub",
                    "target_path": path,
                    "provisional": True,
                    "suggestion": "Wrap model call with surfaced exception path and audit log.",
                }
            )
        elif code == "RNT-08":
            patches.append(
                {
                    "patch_id": f"patch-{code}-validate",
                    "code": code,
                    "action": "add_validation_layer",
                    "target_path": path or "src/",
                    "provisional": True,
                    "suggestion": "Add output validation before downstream tool use.",
                }
            )
        elif code == "GOV-15" and path:
            patches.append(
                {
                    "patch_id": f"patch-{code}-{hash_text(path)[:8]}",
                    "code": code,
                    "action": "annotate_governance_metadata",
                    "target_path": path,
                    "provisional": True,
                    "suggestion": "Add governance header: owner, scope, exception policy.",
                }
            )
    return {
        "schema_version": "patch_plan.v1",
        "case_id": case_id,
        "patch_count": len(patches),
        "patches": patches,
        "safety_state": "dry_run_only",
        "claim_label": "asserted" if patches else "proven",
    }


def build_rebuild_bundle(
    *,
    case_id: str,
    genome: dict[str, Any],
    drifts: list[dict[str, Any]],
) -> dict[str, Any]:
    plan = build_reconstruction_plan(case_id=case_id, drifts=drifts)
    return {
        "mode": "rebuild",
        "case_id": case_id,
        "safety_state": "dry_run_only",
        "target_workflow": build_target_workflow(genome=genome, drifts=drifts),
        "patch_plan": build_patch_plan(case_id=case_id, drifts=drifts, genome=genome),
        "runtime_profile": build_runtime_profile(case_id=case_id, drifts=drifts, genome=genome),
        "reconstruction_plan": plan.model_dump(),
    }
