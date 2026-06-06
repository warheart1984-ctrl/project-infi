"""Mission step → AAIS bridge-cleared deliberation (llm_bridge or full_deliberate)."""

# Mythic: Aais Step Bridge
# Engineering: AaisStepBridgeEngine
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.cognitive_bridge import DECISION_BLOCK, CognitiveBridgeService
from src.jarvis_detachment_guard import build_bridge_attestation
from src.ugr.lane_manager import LaneSpec
from src.ugr.llm_lane import run_governed_llm_lane
from src.ugr.mission.provider_organ import ProviderOrgan
from src.ugr.unified_runtime import UnifiedGovernedRuntime


URG_MISSION_BRIDGE_VERSION = "1.2"
STEP_MODE_LLM_BRIDGE = "llm_bridge"
STEP_MODE_FULL_DELIBERATE = "full_deliberate"


def _runtime_dir(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


def bootstrap_mission_aais(
    runtime_dir: str | Path | None = None,
) -> tuple[CognitiveBridgeService, UnifiedGovernedRuntime]:
    """Bootstrap bridge + UGR runtime for mission step deliberation."""
    from src.immune_system import ImmuneSystemController
    from src.jarvis_detachment_guard import JarvisDetachmentGuard

    root = _runtime_dir(runtime_dir)
    bridge = CognitiveBridgeService(
        immune_controller=ImmuneSystemController(runtime_dir=root),
        detachment_guard=JarvisDetachmentGuard(runtime_dir=root),
    )
    ugr = UnifiedGovernedRuntime(bridge=bridge, runtime_dir=root)
    return bridge, ugr


def mission_step_bridge_enabled(request: dict[str, Any]) -> bool:
    """Default true in v1.2; set aais_step_bridge=false for routing-only."""
    if "aais_step_bridge" in request:
        return bool(request.get("aais_step_bridge"))
    return True


def resolve_step_deliberation_mode(request: dict[str, Any]) -> str:
    mode = str(request.get("step_deliberation_mode") or STEP_MODE_LLM_BRIDGE).strip().lower()
    if mode == STEP_MODE_FULL_DELIBERATE:
        return STEP_MODE_FULL_DELIBERATE
    return STEP_MODE_LLM_BRIDGE


def build_step_question(
    *,
    mission_request: dict[str, Any],
    step: dict[str, Any],
    prior_step_summary: str | None = None,
) -> str:
    """Compose bounded question for bridge + LLM lane."""
    parts = []
    objective = str(mission_request.get("objective") or "").strip()
    if objective:
        parts.append(f"Mission: {objective[:300]}")
    sub = str(step.get("objective") or step.get("sub_goal") or "").strip()
    if sub:
        parts.append(f"Step: {sub[:400]}")
    if prior_step_summary:
        parts.append(f"Prior step: {prior_step_summary[:200]}")
    return " ".join(parts) or "Governed mission step deliberation."


def route_mission_step_bridge(
    *,
    bridge: CognitiveBridgeService,
    mission_request: dict[str, Any],
    ingress: dict[str, Any],
    step: dict[str, Any],
    organ: ProviderOrgan,
    action_id: str,
    mission_id: str,
    prior_action_id: str | None,
    prior_step_summary: str | None,
    runtime_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Real Cognitive Bridge clearance for one mission step."""
    intent = str(mission_request.get("intent") or "governed_super_router_demo").strip().lower()
    question = build_step_question(
        mission_request=mission_request,
        step=step,
        prior_step_summary=prior_step_summary,
    )
    root = _runtime_dir(runtime_dir)
    context = dict(mission_request.get("context") or {})
    context.update(
        {
            "requested_provider": organ.provider,
            "mission_id": mission_id,
            "action_id": action_id,
            "prior_action_id": prior_action_id,
            "organ_id": organ.organ_id,
        }
    )
    bridge_result = bridge.route_to_bridge(
        {
            "source": "urg_mission",
            "type": "deliberation_request",
            "payload": {
                "question": question[:500],
                "intent": intent,
                "execution_intent": "observe",
                "runtime_context": "live_runtime",
                "trace_id": action_id,
                "requested_provider": organ.provider,
                "provider_mode": str(context.get("provider_mode") or organ.provider),
                "bridge_attestation": build_bridge_attestation(
                    ingress="urg_mission",
                    surface="urg_mission_step",
                    source_id=action_id,
                    route="api.ugr.mission.run",
                    intent="observe",
                    runtime_context="live_runtime",
                    packet_type="deliberation_request",
                    runtime_dir=root,
                ),
            },
            "requires_approval": False,
            "risk": str(context.get("risk") or "low"),
        },
        runtime_context="live_runtime",
    )
    return {
        "bridge": bridge_result,
        "question": question,
        "context": context,
        "bridge_attestation_surface": "urg_mission_step",
    }


def run_llm_bridge_step(
    *,
    bridge: CognitiveBridgeService,
    mission_request: dict[str, Any],
    ingress: dict[str, Any],
    step: dict[str, Any],
    organ: ProviderOrgan,
    action_id: str,
    mission_id: str,
    prior_action_id: str | None,
    prior_step_summary: str | None,
    runtime_dir: str | Path | None = None,
    force_execute: bool = False,
) -> dict[str, Any]:
    """Default mode: real bridge + governed LLM lane."""
    routed = route_mission_step_bridge(
        bridge=bridge,
        mission_request=mission_request,
        ingress=ingress,
        step=step,
        organ=organ,
        action_id=action_id,
        mission_id=mission_id,
        prior_action_id=prior_action_id,
        prior_step_summary=prior_step_summary,
        runtime_dir=runtime_dir,
    )
    bridge_result = routed["bridge"]
    decision = str(bridge_result.get("decision") or DECISION_BLOCK).upper()
    if decision == DECISION_BLOCK:
        return {
            "mode": STEP_MODE_LLM_BRIDGE,
            "status": "blocked",
            "bridge_decision": decision,
            "bridge": bridge_result,
            "lane_results": [],
            "governed_llm_status": "BLOCKED",
            "proposal": None,
            "summary": "bridge blocked mission step",
        }

    intent = str(mission_request.get("intent") or "governed_super_router_demo").strip().lower()
    shared_context = {
        "trace_id": action_id,
        "tenant_id": mission_request.get("tenant_id"),
        "intent": intent,
        "question": routed["question"],
        "context": routed["context"],
        "bridge_result": bridge_result,
    }
    lane_spec = LaneSpec(lane_id=f"mission-{action_id}-llm", lane_type="llm")
    lane_result = run_governed_llm_lane(lane_spec, shared_context, force_execute=force_execute)
    lane_dict = lane_result.to_dict()
    governed_llm = dict((lane_dict.get("payload") or {}).get("governed_llm") or {})
    governed_execution = dict((lane_dict.get("payload") or {}).get("governed_llm_execution") or {})
    proposal = governed_llm if governed_llm else None
    provider_execution_status = str(governed_execution.get("status") or governed_llm.get("status") or "")

    return {
        "mode": STEP_MODE_LLM_BRIDGE,
        "status": "ok" if lane_result.status != "blocked" else "blocked",
        "bridge_decision": decision,
        "bridge": bridge_result,
        "lane_results": [lane_dict],
        "governed_llm_status": governed_llm.get("status"),
        "provider_execution_status": provider_execution_status,
        "proposal": proposal,
        "summary": f"llm_bridge step {step.get('step_id')}: {provider_execution_status or governed_llm.get('status')}",
    }


def run_full_deliberate_step(
    *,
    ugr_runtime: UnifiedGovernedRuntime,
    mission_request: dict[str, Any],
    ingress: dict[str, Any],
    step: dict[str, Any],
    organ: ProviderOrgan,
    action_id: str,
    mission_id: str,
    prior_step_summary: str | None,
) -> dict[str, Any]:
    """Full UGR deliberation for one mission step."""
    intent = str(mission_request.get("intent") or "governed_super_router_demo").strip().lower()
    question = build_step_question(
        mission_request=mission_request,
        step=step,
        prior_step_summary=prior_step_summary,
    )
    context = dict(mission_request.get("context") or {})
    context.update(
        {
            "requested_provider": organ.provider,
            "mission_id": mission_id,
            "action_id": action_id,
            "organ_id": organ.organ_id,
        }
    )
    deliberation = ugr_runtime.handle_request(
        {
            "question": question,
            "intent": intent,
            "tenant_id": mission_request.get("tenant_id"),
            "context": context,
            "lane_types": list(mission_request.get("lane_types") or []),
        }
    )
    bridge = dict(deliberation.get("bridge") or {})
    decision = str(bridge.get("decision") or deliberation.get("status") or "unknown").upper()
    lane_results = list(deliberation.get("lane_results") or [])
    governed_llm_status = None
    proposal = None
    for lane in lane_results:
        if lane.get("lane_type") != "llm":
            continue
        envelope = dict((lane.get("payload") or {}).get("governed_llm") or {})
        if envelope:
            governed_llm_status = envelope.get("status")
            proposal = envelope
            break

    blocked = deliberation.get("status") in {"blocked", "rejected"} or decision == DECISION_BLOCK
    return {
        "mode": STEP_MODE_FULL_DELIBERATE,
        "status": "blocked" if blocked else "ok",
        "bridge_decision": decision,
        "bridge": bridge,
        "deliberation": deliberation,
        "lane_results": lane_results,
        "governed_llm_status": governed_llm_status,
        "proposal": proposal,
        "summary": deliberation.get("summary"),
    }


def run_mission_step_deliberation(
    *,
    mission_request: dict[str, Any],
    ingress: dict[str, Any],
    step: dict[str, Any],
    organ: ProviderOrgan,
    action_id: str,
    mission_id: str,
    prior_action_id: str | None = None,
    prior_step_summary: str | None = None,
    bridge: CognitiveBridgeService | None = None,
    ugr_runtime: UnifiedGovernedRuntime | None = None,
    runtime_dir: str | Path | None = None,
    force_execute: bool = False,
) -> dict[str, Any]:
    """Execute AAIS deliberation for one mission step."""
    mode = resolve_step_deliberation_mode(mission_request)
    root = _runtime_dir(runtime_dir)
    if bridge is None or (mode == STEP_MODE_FULL_DELIBERATE and ugr_runtime is None):
        bridge_svc, ugr_rt = bootstrap_mission_aais(root)
        bridge = bridge or bridge_svc
        ugr_runtime = ugr_runtime or ugr_rt

    if mode == STEP_MODE_FULL_DELIBERATE:
        result = run_full_deliberate_step(
            ugr_runtime=ugr_runtime,  # type: ignore[arg-type]
            mission_request=mission_request,
            ingress=ingress,
            step=step,
            organ=organ,
            action_id=action_id,
            mission_id=mission_id,
            prior_step_summary=prior_step_summary,
        )
    else:
        result = run_llm_bridge_step(
            bridge=bridge,  # type: ignore[arg-type]
            mission_request=mission_request,
            ingress=ingress,
            step=step,
            organ=organ,
            action_id=action_id,
            mission_id=mission_id,
            prior_action_id=prior_action_id,
            prior_step_summary=prior_step_summary,
            runtime_dir=root,
            force_execute=force_execute,
        )

    return {
        "bridge_version": URG_MISSION_BRIDGE_VERSION,
        "step_deliberation_mode": mode,
        **result,
    }
