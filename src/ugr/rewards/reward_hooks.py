"""Runtime hooks — emit operator rewards from governed contribution events."""

# Mythic: Reward Hooks
# Engineering: RewardHooksEngine
from __future__ import annotations

import os
from typing import Any


def _runtime_dir() -> str | None:
    return os.getenv("AAIS_RUNTIME_DIR") or None


def _safe_emit(result: dict[str, Any]) -> dict[str, Any]:
    try:
        return result
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}


def emit_provider_organ_admitted(
    *,
    tenant_id: str,
    operator_id: str,
    organ_id: str,
    governance_mission_id: str,
    aais_instance_id: str = "aais-local",
) -> dict[str, Any]:
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine
    from src.ugr.rewards.operator_reward_spec import EVENT_PROVIDER_ORGAN_ADMITTED

    return _safe_emit(
        build_operator_reward_engine(_runtime_dir()).maybe_issue(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_type="organ",
            payload={
                "organ_id": organ_id,
                "governance_mission_id": governance_mission_id,
            },
            event_type=EVENT_PROVIDER_ORGAN_ADMITTED,
            aais_instance_id=aais_instance_id,
            governance_mission_id=governance_mission_id,
            governance_status="ok",
        )
    )


def emit_cloud_invariant_set_passed(
    *,
    tenant_id: str,
    operator_id: str,
    mission_id: str,
    invariant_digest: str,
    invariant_version: str | None = None,
    aais_instance_id: str = "aais-local",
) -> dict[str, Any]:
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine
    from src.ugr.rewards.operator_reward_spec import EVENT_CLOUD_INVARIANT_SET_PASSED

    return _safe_emit(
        build_operator_reward_engine(_runtime_dir()).maybe_issue(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_type="invariant",
            payload={
                "mission_id": mission_id,
                "invariant_digest": invariant_digest,
                "invariant_version": invariant_version,
                "all_passed": True,
            },
            event_type=EVENT_CLOUD_INVARIANT_SET_PASSED,
            aais_instance_id=aais_instance_id,
        )
    )


def emit_workflow_chain_completed(
    *,
    tenant_id: str,
    operator_id: str,
    workflow_id: str,
    run_id: str,
    step_count: int,
    dry_run: bool = False,
    aais_instance_id: str = "aais-local",
) -> dict[str, Any]:
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine
    from src.ugr.rewards.operator_reward_spec import EVENT_WORKFLOW_CHAIN_COMPLETED

    return _safe_emit(
        build_operator_reward_engine(_runtime_dir()).maybe_issue(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_type="workflow",
            payload={
                "workflow_id": workflow_id,
                "run_id": run_id,
                "step_count": step_count,
                "dry_run": dry_run,
            },
            event_type=EVENT_WORKFLOW_CHAIN_COMPLETED,
            aais_instance_id=aais_instance_id,
        )
    )


def emit_capability_bridge_executed(
    *,
    tenant_id: str,
    operator_id: str,
    trace_id: str,
    module: str,
    action: str,
    audit_sequence: int | None = None,
    ok: bool = True,
    aais_instance_id: str = "aais-local",
) -> dict[str, Any]:
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine
    from src.ugr.rewards.operator_reward_spec import EVENT_CAPABILITY_BRIDGE_EXECUTED

    return _safe_emit(
        build_operator_reward_engine(_runtime_dir()).maybe_issue(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_type="capability",
            payload={
                "trace_id": trace_id,
                "module": module,
                "action": action,
                "audit_sequence": audit_sequence,
                "ok": ok,
            },
            event_type=EVENT_CAPABILITY_BRIDGE_EXECUTED,
            aais_instance_id=aais_instance_id,
        )
    )


def emit_pattern_claim_accepted(
    *,
    tenant_id: str,
    operator_id: str,
    claim_id: str,
    classification: str = "accepted",
    aais_instance_id: str = "aais-local",
) -> dict[str, Any]:
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine
    from src.ugr.rewards.operator_reward_spec import EVENT_PATTERN_CLAIM_ACCEPTED

    return _safe_emit(
        build_operator_reward_engine(_runtime_dir()).maybe_issue(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_type="substrate",
            payload={
                "claim_id": claim_id,
                "classification": classification,
                "status": classification,
            },
            event_type=EVENT_PATTERN_CLAIM_ACCEPTED,
            aais_instance_id=aais_instance_id,
        )
    )


def emit_substrate_envelope_attached(
    *,
    tenant_id: str,
    operator_id: str,
    trace_id: str,
    surface: str,
    aais_instance_id: str = "aais-local",
) -> dict[str, Any]:
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine
    from src.ugr.rewards.operator_reward_spec import EVENT_SUBSTRATE_ENVELOPE_ATTACHED

    return _safe_emit(
        build_operator_reward_engine(_runtime_dir()).maybe_issue(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_type="substrate",
            payload={
                "substrate_id": "aais.ul_substrate",
                "surface": surface,
                "trace_id": trace_id,
            },
            event_type=EVENT_SUBSTRATE_ENVELOPE_ATTACHED,
            aais_instance_id=aais_instance_id,
        )
    )
