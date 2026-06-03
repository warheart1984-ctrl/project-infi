"""Step execution lifecycle — planned → dispatched → committed."""

from __future__ import annotations

from hashlib import sha256
import json
import time
from typing import Any

from src.ugr.invariants.execution_safety import check_execution_safety
from src.ugr.mission.execution_policy import (
    EXECUTION_MODE_DRY_RUN,
    EXECUTION_STATE_COMMITTED,
    EXECUTION_STATE_DISPATCHED,
    EXECUTION_STATE_PLANNED,
    EXECUTION_STATE_SIMULATED,
    execution_results_downstream,
    is_shadow_execution,
    provider_calls_allowed,
)
from src.ugr.mission.mission_ledger import MissionLedger


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def provider_execution_status(aais_deliberation: dict[str, Any] | None) -> str:
    """Provider ack follows governed_llm_execution.status, not envelope PROPOSED."""
    if not aais_deliberation:
        return ""
    for lane in list(aais_deliberation.get("lane_results") or []):
        execution = dict((lane.get("payload") or {}).get("governed_llm_execution") or {})
        status = str(execution.get("status") or "").strip()
        if status:
            return status
    return str(aais_deliberation.get("governed_llm_status") or "").strip()


def payload_digest(payload: dict[str, Any]) -> str:
    """SHA256 of provider-bound payload metadata (not raw secrets)."""
    canonical = {
        "provider": payload.get("provider"),
        "organ_id": payload.get("organ_id"),
        "step_id": payload.get("step_id"),
        "status": payload.get("status"),
        "proposal_status": payload.get("proposal_status"),
        "execution_state": payload.get("execution_state"),
    }
    return sha256(_stable_json(canonical).encode("utf-8")).hexdigest()


def build_ledger_phase_record(
    *,
    phase: str,
    mission_id: str,
    action_id: str,
    step_id: str,
    provider: str | None = None,
    organ_id: str | None = None,
    execution_state: str | None = None,
    payload: dict[str, Any] | None = None,
    shadow: bool = False,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = dict(extra or {})
    body.update(
        {
            "type": "urg_mission_transition",
            "phase": phase,
            "mission_id": mission_id,
            "action_id": action_id,
            "step_id": step_id,
            "timestamp": int(time.time()),
            "provider": provider,
            "organ_id": organ_id,
            "execution_state": execution_state,
            "shadow": shadow,
        }
    )
    if payload:
        body["payload_digest"] = payload_digest(payload)
    return body


def append_mission_ingress_ledger(
    ledger: MissionLedger,
    *,
    mission_id: str,
    ingress: dict[str, Any],
    cloud_manifold: dict[str, Any],
) -> str:
    action_id = f"{mission_id}:ingress:0"
    record = build_ledger_phase_record(
        phase="mission_ingress",
        mission_id=mission_id,
        action_id=action_id,
        step_id="ingress",
        extra={
            "ingress_stamp_hash": ingress.get("stamp_hash"),
            "cloud_identity_hash": cloud_manifold.get("cloud_identity_hash"),
            "boundary_digest": cloud_manifold.get("boundary_digest"),
        },
    )
    return ledger.append_action(record)


def append_organ_assignment_ledger(
    ledger: MissionLedger,
    *,
    mission_id: str,
    step_id: str,
    organ_id: str,
    provider: str,
    ordinal: int,
) -> str:
    action_id = f"{mission_id}:{step_id}:assign:{ordinal}"
    record = build_ledger_phase_record(
        phase="organ_assignment",
        mission_id=mission_id,
        action_id=action_id,
        step_id=step_id,
        organ_id=organ_id,
        provider=provider,
        execution_state=EXECUTION_STATE_PLANNED,
    )
    return ledger.append_action(record)


def run_step_execution(
    *,
    execution_mode: str,
    mission_request: dict[str, Any],
    step: dict[str, Any],
    organ: Any,
    action_id: str,
    mission_id: str,
    ingress: dict[str, Any],
    manifold: Any,
    invariants: Any,
    ledger: MissionLedger,
    prior_action_id: str | None,
    rail: str,
    run_bridge_fn: Any,
    step_invariants: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Execute one step under execution policy.

    Returns step outcome dict with execution_state, execution_committed, shadow.
    """
    from src.cognitive_bridge import DECISION_BLOCK

    step_id = str(step.get("step_id") or "")
    provider = organ.provider
    shadow = is_shadow_execution(execution_mode)
    execution_state = EXECUTION_STATE_PLANNED

    dispatch_record = build_ledger_phase_record(
        phase="provider_dispatch",
        mission_id=mission_id,
        action_id=action_id,
        step_id=step_id,
        provider=provider,
        organ_id=organ.organ_id,
        execution_state=EXECUTION_STATE_DISPATCHED if provider_calls_allowed(execution_mode) else EXECUTION_STATE_PLANNED,
        shadow=shadow,
        extra={"rail": rail, "simulated": execution_mode == EXECUTION_MODE_DRY_RUN},
    )
    if provider_calls_allowed(execution_mode):
        ledger.append_action(dispatch_record)
        execution_state = EXECUTION_STATE_DISPATCHED

    aais_deliberation = None
    proposal = None
    step_status = "ok"

    aais_deliberation = run_bridge_fn()
    proposal = aais_deliberation.get("proposal")
    bridge_decision = str(aais_deliberation.get("bridge_decision") or "").upper()
    if aais_deliberation.get("status") == "blocked" or bridge_decision == DECISION_BLOCK:
        step_status = "blocked"

    if execution_mode == EXECUTION_MODE_DRY_RUN:
        execution_state = EXECUTION_STATE_SIMULATED
        if not proposal:
            proposal = {
                "status": "SIMULATED",
                "proposal_only": True,
                "execution_authority": "none",
                "simulated": True,
            }

    provider_ack = None
    execution_committed = False
    governed_status = str((aais_deliberation or {}).get("governed_llm_status") or "")
    execution_status = provider_execution_status(aais_deliberation)

    if step_status == "ok" and provider_calls_allowed(execution_mode):
        provider_ack = {
            "provider": provider,
            "organ_id": organ.organ_id,
            "step_id": step_id,
            "governed_llm_status": governed_status,
            "provider_execution_status": execution_status,
            "provider_acknowledged": execution_status == "EXECUTED",
            "shadow": shadow,
        }
        commit_ok, commit_state, safety_results = try_commit_execution(
            mission_request=mission_request,
            ingress=ingress,
            step=step,
            organ=organ,
            action_id=action_id,
            mission_id=mission_id,
            manifold=manifold,
            invariants=invariants,
            step_invariants=step_invariants,
            rail=rail,
            provider_ack=provider_ack,
            pending_receipt=True,
        )
        if commit_ok:
            execution_state = commit_state
            execution_committed = commit_state == EXECUTION_STATE_COMMITTED
            ack_record = build_ledger_phase_record(
                phase="provider_ack",
                mission_id=mission_id,
                action_id=action_id,
                step_id=step_id,
                provider=provider,
                organ_id=organ.organ_id,
                execution_state=execution_state,
                payload=provider_ack,
                shadow=shadow,
                extra={"governed_llm_status": governed_status},
            )
            ledger.append_action(ack_record)
        else:
            step_status = "blocked"
            if aais_deliberation:
                aais_deliberation["execution_safety"] = safety_results
    elif step_status == "ok" and execution_mode == EXECUTION_MODE_DRY_RUN:
        sim_record = build_ledger_phase_record(
            phase="provider_ack",
            mission_id=mission_id,
            action_id=action_id,
            step_id=step_id,
            provider=provider,
            organ_id=organ.organ_id,
            execution_state=EXECUTION_STATE_SIMULATED,
            shadow=False,
            extra={"simulated": True},
        )
        ledger.append_action(sim_record)

    if not execution_results_downstream(execution_mode) and aais_deliberation:
        aais_deliberation = dict(aais_deliberation)
        aais_deliberation["downstream_discarded"] = True
        if "governed_llm_execution" in aais_deliberation:
            aais_deliberation.pop("governed_llm_execution", None)

    return {
        "step_status": step_status,
        "execution_state": execution_state,
        "execution_committed": execution_committed,
        "shadow": shadow,
        "aais_deliberation": aais_deliberation,
        "proposal": proposal,
        "provider_ack": provider_ack,
    }


def try_commit_execution(
    *,
    mission_request: dict[str, Any],
    ingress: dict[str, Any],
    step: dict[str, Any],
    organ: Any,
    action_id: str,
    mission_id: str,
    manifold: Any,
    invariants: Any,
    step_invariants: list[dict[str, Any]],
    rail: str,
    provider_ack: dict[str, Any],
    pending_receipt: bool = True,
) -> tuple[bool, str, list[dict[str, Any]]]:
    """
    Promote step to execution_committed when safety + invariants pass.

    execution_committed = provider ack + ledger write + invariants satisfied.
    """
    if not provider_ack.get("provider_acknowledged"):
        return False, EXECUTION_STATE_DISPATCHED, [
            {"family": "cloud_execution_safety", "status": "hard_fail", "details": "no provider ack"}
        ]

    if invariants.has_hard_fail(step_invariants):
        return False, EXECUTION_STATE_DISPATCHED, step_invariants

    mission_state = {
        "request": mission_request,
        "ingress": ingress,
        "region_id": mission_request.get("region_id"),
        "cloud_manifold": manifold.to_dict() if hasattr(manifold, "to_dict") else dict(manifold or {}),
    }
    assignment = {
        "organ_id": organ.organ_id,
        "provider": organ.provider,
        "rail": rail,
    }
    safety = check_execution_safety(
        mission_state,
        assignment,
        manifold=manifold,
        ledger_write_ok=True,
        pending_receipt=pending_receipt,
    )
    from src.ugr.invariants.cloud_invariants import has_hard_fail as _has_hard_fail

    if _has_hard_fail(safety):
        return False, EXECUTION_STATE_DISPATCHED, safety

    return True, EXECUTION_STATE_COMMITTED, safety


