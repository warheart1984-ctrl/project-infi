"""Forge, evolve, and repo-mutation paths through Project Infi with CISIV staging."""

# Mythic: Forge Repo Governance
# Engineering: ForgeRepoGovernanceEngine
from __future__ import annotations

from typing import Any

from src.cisiv import CISIV_STAGE_SEQUENCE, normalize_cisiv_stage

FORGE_CONTRACTOR_SURFACE = "forge_contractor"
FORGE_EVAL_SURFACE = "forge_eval"
EVOLVE_CONTRACTOR_SURFACE = "evolve_contractor"
REPO_ACTION_SURFACE = "repo_action"
FORGE_REPO_CONTRACT_VERSION = "aais.forge_repo_governance.v1"


def infer_forge_cisiv_stage(kind: str | None) -> str:
    """Map one Forge contractor kind to a canonical CISIV stage."""
    normalized = str(kind or "").strip().lower()
    if normalized == "analyze":
        return normalize_cisiv_stage("concept")
    if normalized in {"generate_diff", "generate_code", "generate_tests"}:
        return normalize_cisiv_stage("structure")
    if normalized == "repo_manager":
        return normalize_cisiv_stage("implementation")
    return normalize_cisiv_stage("implementation")


def infer_patch_review_cisiv_stage(*, phase: str = "create") -> str:
    """Map one patch-review phase to a canonical CISIV stage."""
    mapping = {
        "create": "structure",
        "preview": "structure",
        "decision": "verification",
        "apply": "implementation",
    }
    return normalize_cisiv_stage(mapping.get(str(phase or "").strip().lower(), "structure"))


def infer_evolve_cisiv_stage(*, phase: str = "run") -> str:
    """Map one evolve lane phase to a canonical CISIV stage."""
    mapping = {
        "run": "structure",
        "handoff": "implementation",
        "verify": "verification",
    }
    return normalize_cisiv_stage(mapping.get(str(phase or "").strip().lower(), "structure"))


def _project_infi_law():
    from src.jarvis_operator import jarvis_operator

    return jarvis_operator.project_infi_law


def finalize_contractor_runtime_action(
    *,
    surface: str,
    action_id: str,
    target: str,
    cisiv_stage: str,
    result: dict[str, Any] | None,
    summary: str,
    details: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str = "jarvis_operator",
    actor_role: str = "system",
    finalize_details: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run Project Infi admission for one non-repo contractor action."""
    project_infi_law = _project_infi_law()
    contract, ul_snapshot, _ = project_infi_law.require_contract(
        surface=surface,
        action_id=action_id,
        actor_id=actor_id,
        actor_role=actor_role,
        session_id=session_id,
        target=target,
        repo_change=False,
        verification_plan=None,
        run_id=None,
        cisiv_stage=normalize_cisiv_stage(cisiv_stage),
        details={
            "contract_version": FORGE_REPO_CONTRACT_VERSION,
            **dict(details or {}),
        },
    )
    result_status = str((result or {}).get("status") or "completed").strip().lower() or "completed"
    if (result or {}).get("ok") is False and result_status == "completed":
        result_status = "failed"
    law_enforcement, law_event_log = project_infi_law.finalize_runtime_action(
        contract,
        action_status=result_status,
        summary=summary,
        actor_id=actor_id,
        actor_role=actor_role,
        details={
            "cisiv_stage": normalize_cisiv_stage(cisiv_stage),
            **dict(finalize_details or {}),
        },
    )
    try:
        from src.ul_lineage import record_lineage_event

        record_lineage_event(
            node_type="forge_handoff",
            cisiv_stage=normalize_cisiv_stage(cisiv_stage),
            session_id=session_id,
            law_enforcement=law_enforcement,
            claim_label="asserted",
            source_module="src.forge_repo_governance",
            payload={"action_id": action_id, "surface": surface},
        )
    except Exception:
        pass
    return law_enforcement, ul_snapshot, law_event_log


def wrap_contractor_governed_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach UL substrate to one governed contractor payload."""
    from src.aais_ul.runtime import wrap_contractor_payload

    wrapped = wrap_contractor_payload(dict(payload))
    wrapped["cisiv_stage"] = payload.get("cisiv_stage")
    wrapped["cisiv_stage_sequence"] = list(CISIV_STAGE_SEQUENCE)
    return wrapped


def govern_patch_review_record(
    review: dict[str, Any],
    *,
    phase: str,
    action_id: str,
    details: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Attach Project Infi admission metadata to one patch review record."""
    review_id = str(review.get("id") or "").strip()
    cisiv_stage = infer_patch_review_cisiv_stage(phase=phase)
    law_enforcement, ul_snapshot, law_event_log = finalize_contractor_runtime_action(
        surface=REPO_ACTION_SURFACE,
        action_id=action_id,
        target=review_id or "patch_review",
        cisiv_stage=cisiv_stage,
        result={"status": "completed", "ok": True},
        summary=str(review.get("goal") or review_id or "Patch review updated."),
        session_id=session_id or str(review.get("session_id") or "").strip() or None,
        details={
            "review_id": review_id,
            "review_status": review.get("status"),
            "phase": phase,
            **dict(details or {}),
        },
        finalize_details={
            "review_id": review_id,
            "phase": phase,
        },
    )
    enriched = dict(review)
    enriched["law_enforcement"] = law_enforcement
    enriched["ul_snapshot"] = ul_snapshot
    enriched["law_event_log"] = law_event_log
    enriched["cisiv_stage"] = cisiv_stage
    enriched["cisiv_stage_sequence"] = list(CISIV_STAGE_SEQUENCE)
    return wrap_contractor_governed_payload(enriched)


def govern_evolution_job_payload(
    *,
    task: str,
    preset: str,
    result: dict[str, Any],
    job_id: str,
    jarvis_run_id: str | None = None,
    config: dict[str, Any] | None = None,
    evaluation: dict[str, Any] | None = None,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Layer Project Infi admission over one EvolveEngine handoff."""
    cisiv_stage = infer_evolve_cisiv_stage(phase="run")
    service_law = dict(result.get("law_enforcement") or {})
    service_ul = dict(result.get("ul_snapshot") or {})
    law_enforcement, ul_snapshot, law_event_log = finalize_contractor_runtime_action(
        surface=EVOLVE_CONTRACTOR_SURFACE,
        action_id=str(preset or "evolve_job"),
        target=job_id,
        cisiv_stage=cisiv_stage,
        result=result,
        summary=str(result.get("summary") or task or f"Evolve job {job_id} completed."),
        details={
            "job_id": job_id,
            "preset": preset,
            "jarvis_run_id": jarvis_run_id,
            "service_contract_version": service_law.get("contract_version"),
        },
        finalize_details={
            "job_id": job_id,
            "preset": preset,
            "jarvis_run_id": jarvis_run_id,
        },
    )
    merged_ul = ul_snapshot or service_ul
    if service_ul.get("payloads"):
        ingress_payloads = list(merged_ul.get("payloads") or [])
        for item in list(service_ul.get("payloads") or []):
            if item not in ingress_payloads:
                ingress_payloads.append(item)
        merged_ul = {
            **merged_ul,
            "count": max(int(merged_ul.get("count") or 0), int(service_ul.get("count") or 0)),
            "sections": list(
                dict.fromkeys(
                    list(merged_ul.get("sections") or []) + list(service_ul.get("sections") or [])
                )
            ),
            "payloads": ingress_payloads,
        }
    payload = {
        "job_id": job_id,
        "task": task,
        "preset": preset,
        "config": dict(config or {}),
        "evaluation": dict(evaluation or {}),
        "constraints": dict(constraints or {}),
        "result": result,
        "service_law_enforcement": service_law or None,
        "service_ul_snapshot": service_ul or None,
        "law_enforcement": law_enforcement,
        "ul_snapshot": merged_ul,
        "law_event_log": law_event_log,
        "cisiv_stage": cisiv_stage,
        "cisiv_stage_sequence": list(CISIV_STAGE_SEQUENCE),
    }
    return wrap_contractor_governed_payload(payload)


def build_forge_contractor_payload(
    *,
    task_id: str,
    task: str,
    kind: str,
    result: dict[str, Any],
    forge_context: dict[str, Any],
    auto_approve: bool,
    law_enforcement: dict[str, Any],
    ul_snapshot: dict[str, Any],
    law_event_log: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one governed Forge contractor response payload."""
    cisiv_stage = infer_forge_cisiv_stage(kind)
    payload = {
        "task_id": task_id,
        "task": task,
        "kind": kind,
        "result": result,
        "auto_approve": auto_approve,
        "forge_context": forge_context,
        "law_enforcement": law_enforcement,
        "ul_snapshot": ul_snapshot,
        "law_event_log": law_event_log,
        "cisiv_stage": cisiv_stage,
        "cisiv_stage_sequence": list(CISIV_STAGE_SEQUENCE),
        **dict(extra or {}),
    }
    return wrap_contractor_governed_payload(payload)


def build_forge_eval_payload(
    *,
    task_id: str,
    mode: str,
    result: dict[str, Any],
    law_enforcement: dict[str, Any],
    ul_snapshot: dict[str, Any],
    law_event_log: dict[str, Any],
) -> dict[str, Any]:
    """Build one governed ForgeEval response payload."""
    payload = {
        "task_id": task_id,
        "mode": mode,
        "result": result,
        "law_enforcement": law_enforcement,
        "ul_snapshot": ul_snapshot,
        "law_event_log": law_event_log,
        "cisiv_stage": infer_forge_cisiv_stage("analyze"),
        "cisiv_stage_sequence": list(CISIV_STAGE_SEQUENCE),
    }
    return wrap_contractor_governed_payload(payload)
