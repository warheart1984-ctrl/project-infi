"""UGR discovery, rewards, and mission routes through Project Infi admission."""

# Mythic: Ugr Runtime Governance
# Engineering: UgrRuntimeGovernanceEngine
from __future__ import annotations

from typing import Any

from src.cisiv import normalize_cisiv_stage

UGR_DISCOVERY_SURFACE = "ugr_discovery"
UGR_REWARD_SURFACE = "ugr_reward"
UGR_MISSION_SURFACE = "ugr_mission"
UGR_RUNTIME_CONTRACT_VERSION = "aais.ugr_runtime_governance.v1"


def _project_infi_law():
    from src.jarvis_operator import jarvis_operator

    return jarvis_operator.project_infi_law


def infer_ugr_cisiv_stage(*, surface: str, phase: str = "execute") -> str:
    """Map one UGR surface phase to a canonical CISIV stage."""
    normalized_surface = str(surface or "").strip().lower()
    normalized_phase = str(phase or "").strip().lower()
    if normalized_surface == UGR_DISCOVERY_SURFACE:
        return normalize_cisiv_stage("verification")
    if normalized_surface == UGR_REWARD_SURFACE:
        mapping = {
            "issue": "verification",
            "transfer": "implementation",
            "exchange": "implementation",
            "spend": "implementation",
        }
        return normalize_cisiv_stage(mapping.get(normalized_phase, "verification"))
    if normalized_surface == UGR_MISSION_SURFACE:
        mapping = {
            "run": "implementation",
            "governance": "verification",
        }
        return normalize_cisiv_stage(mapping.get(normalized_phase, "implementation"))
    return normalize_cisiv_stage("verification")


def finalize_ugr_runtime_action(
    *,
    surface: str,
    action_id: str,
    target: str,
    result: dict[str, Any] | None,
    summary: str,
    cisiv_stage: str | None = None,
    actor_id: str = "ugr_runtime",
    actor_role: str = "operator",
    session_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run Project Infi admission for one UGR runtime action."""
    stage = normalize_cisiv_stage(cisiv_stage or infer_ugr_cisiv_stage(surface=surface))
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
        cisiv_stage=stage,
        details={
            "contract_version": UGR_RUNTIME_CONTRACT_VERSION,
            **dict(details or {}),
        },
    )
    result_status = str((result or {}).get("status") or "completed").strip().lower() or "completed"
    if (result or {}).get("ok") is False and result_status in {"completed", "ok"}:
        result_status = "failed"
    if result_status in {"discovered", "issued", "transferred", "exchanged", "spent"}:
        result_status = "completed"
    law_enforcement, law_event_log = project_infi_law.finalize_runtime_action(
        contract,
        action_status=result_status,
        summary=summary,
        actor_id=actor_id,
        actor_role=actor_role,
        details={"cisiv_stage": stage, **dict(details or {})},
    )
    return law_enforcement, ul_snapshot, law_event_log


def attach_ugr_law_enforcement(payload: dict[str, Any], law_enforcement: dict[str, Any]) -> dict[str, Any]:
    """Attach governed law metadata to one UGR API payload."""
    wrapped = dict(payload)
    wrapped["law_enforcement"] = dict(law_enforcement)
    try:
        from src.aais_ul_substrate import attach_ul_substrate

        return attach_ul_substrate(wrapped)
    except Exception:
        return wrapped
