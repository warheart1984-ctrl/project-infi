"""Governed direct pipeline packet contracts for AAIS.

This module turns the direct internal pipeline design into executable,
inspectable packet traces without replacing the existing runtime. The goal is
to make core cognitive traffic explicit and keep slower service/tool work off
the fast lane.
"""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
from typing import Any
from uuid import uuid4

from src.continuity_witness import build_continuity_witness_input
from src.immune_protocol import apply_immune_protocol


PIPELINE_ID = "aais.governed_direct_pipeline"
PIPELINE_VERSION = "0.1"
DIRECT_COGNITIVE_LANE = "direct_cognitive"
SERVICE_TOOL_LANE = "service_tools"

NODE_LABELS = {
    "llm": "LLM",
    "gb": "God Brain",
    "jar": "Jarvis",
    "nov": "Nova",
    "pred": "Predictor",
    "svc": "Service Lane",
}

PRIORITY_CODES = {
    "critical": 1,
    "high": 2,
    "normal": 3,
    "low": 4,
}

STATE_CODES = {
    "unknown": 0,
    "stable": 1,
    "active": 2,
    "caution": 3,
    "elevated": 4,
    "degraded": 5,
    "blocked": 6,
    "hold": 7,
}

OPERATION_CODES = {
    "sync": 1,
    "respond": 2,
    "route": 3,
    "hold": 4,
    "escalate": 5,
    "state_delta": 6,
    "request": 7,
    "result": 8,
    "ack": 9,
    "ref_pull": 11,
    "ref_push": 12,
    "tool_call": 13,
    "tool_result": 14,
    "approve": 16,
    "express": 18,
    "verify": 19,
    "predict_event": 22,
    "predict_cause": 23,
}

TONE_CODES = {
    "neutral": 0,
    "operator": 1,
    "analytical": 2,
    "companion": 3,
    "calm": 4,
    "urgent": 5,
    "gentle": 6,
}

LIMIT_CODES = {
    "none": 0,
    "no_tools": 1,
    "no_memory_write": 2,
    "no_external": 3,
    "user_facing_only": 4,
    "operator_only": 5,
    "bounded_reply": 6,
    "service_lane_only": 7,
}

REALTIME_SIGNAL_FEED_ID = "aais.governed_direct_pipeline.realtime_signal_feed"
REALTIME_SIGNAL_FEED_VERSION = "0.1"
MAX_REALTIME_SIGNALS = 7
REALTIME_SIGNAL_REQUIRED_KEYS = (
    "signal_type",
    "signal_class",
    "stable_key",
    "severity",
    "status",
    "data_sufficiency",
    "attributes",
)
TURN_DELTA_KEYS = (
    "has_previous_turn",
    "runtime_context_changed",
    "lane_changed",
    "traffic_class_changed",
    "response_mode_changed",
    "contract_changed",
    "tool_changed",
    "immune_response_changed",
    "system_mode_changed",
    "risk_level_changed",
    "surface_node_changed",
    "change_count",
    "stable_repeat",
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_runtime_context(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return normalized or "live_runtime"


def _node_label(node: str) -> str:
    normalized = str(node or "").strip().lower()
    return NODE_LABELS.get(normalized, normalized or "Unknown")


def _priority_for_turn(response_mode: str, tool_result: dict[str, Any] | None) -> str:
    normalized_mode = str(response_mode or "fast").strip().lower()
    tool_type = str((tool_result or {}).get("type") or "").strip().lower()
    if tool_type in {"action_request", "action_result", "lane_guardrail"}:
        return "critical"
    if tool_result:
        return "high"
    if normalized_mode in {"debug", "operator"}:
        return "high"
    return "normal"


def _state_from_posture(god_brain: dict[str, Any] | None) -> str:
    summary = str((god_brain or {}).get("authority_summary") or "").lower()
    if "degraded" in summary:
        return "degraded"
    if "cautious" in summary or "caution" in summary:
        return "caution"
    return "stable"


def _tone_for_turn(response_mode: str, surface_node: str) -> str:
    normalized_mode = str(response_mode or "fast").strip().lower()
    if surface_node == "nov":
        return "companion" if normalized_mode in {"tiny", "small"} else "calm"
    if normalized_mode in {"debug", "research"}:
        return "analytical"
    if normalized_mode == "operator":
        return "operator"
    return "neutral"


def _surface_node(surface_identity: str | None, response_mode: str) -> str:
    normalized_surface = str(surface_identity or "").strip().lower()
    normalized_mode = str(response_mode or "fast").strip().lower()
    if normalized_surface in {"nova", "nov", "tiny_nova", "small_nova"}:
        return "nov"
    if normalized_mode in {"tiny", "small"}:
        return "nov"
    return "jar"


def _route_for_surface(surface_node: str) -> list[str]:
    if surface_node == "nov":
        return ["llm", "gb", "jar", "nov"]
    return ["llm", "gb", "jar"]


def _return_route_for_surface(surface_node: str) -> list[str]:
    if surface_node == "nov":
        return ["nov", "jar", "gb", "llm"]
    return ["jar", "gb", "llm"]


def _constraint_codes(constraints: list[str]) -> list[int]:
    codes: list[int] = []
    for constraint in constraints:
        code = LIMIT_CODES.get(str(constraint or "").strip().lower())
        if code is not None:
            codes.append(code)
    return codes or [0]


def _compact_channel_for_lane(lane_name: str) -> str:
    return "core" if lane_name == DIRECT_COGNITIVE_LANE else "svc"


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _packet_payload(
    *,
    meaning: str,
    tone: str,
    constraints: list[str],
    summary: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "meaning": meaning,
        "constraints": list(constraints or []),
        "tone": tone,
    }
    if summary:
        payload["summary"] = summary
    if metadata:
        payload["metadata"] = dict(metadata)
    return payload


def build_pipeline_packet(
    *,
    source: str,
    target: str,
    lane: str,
    priority: str,
    intent: str,
    state: dict[str, Any],
    payload: dict[str, Any],
    route: list[str],
    ref: str | None = None,
    compact_channel: str | None = None,
    compact_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one inspectable packet plus a compact transport view."""
    packet_id = f"pkt_{uuid4().hex}"
    timestamp = _now_iso()
    source_node = str(source or "").strip().lower()
    target_node = str(target or "").strip().lower()
    lane_name = str(lane or DIRECT_COGNITIVE_LANE).strip().lower()
    priority_name = str(priority or "normal").strip().lower()
    compact_lane = (
        str(compact_channel or _compact_channel_for_lane(lane_name)).strip().lower()
        or _compact_channel_for_lane(lane_name)
    )
    compact_tone = TONE_CODES.get(str(payload.get("tone") or "neutral").strip().lower(), 0)
    compact_state = STATE_CODES.get(str(state.get("system_mode") or "stable").strip().lower(), 1)
    compact_op = OPERATION_CODES.get(str(intent or "sync").strip().lower(), 1)
    compact_priority = PRIORITY_CODES.get(priority_name, 3)
    compact_ref = str(ref or payload.get("metadata", {}).get("contract") or "").strip() or None
    compact_body = {
        "m": str(payload.get("meaning") or "").strip().lower().replace(" ", "_"),
        "t": compact_tone,
        "lim": _constraint_codes(list(payload.get("constraints") or [])),
    }
    if isinstance(compact_payload, dict):
        compact_body.update(dict(compact_payload))

    return {
        "packet_id": packet_id,
        "timestamp": timestamp,
        "source": source_node,
        "source_label": _node_label(source_node),
        "target": target_node,
        "target_label": _node_label(target_node),
        "lane": lane_name,
        "priority": priority_name,
        "intent": str(intent or "sync").strip().lower(),
        "state": {
            "user_mode": str(state.get("user_mode") or "").strip().lower() or "normal",
            "system_mode": str(state.get("system_mode") or "").strip().lower() or "stable",
            "risk_level": str(state.get("risk_level") or "").strip().lower() or "low",
        },
        "payload": dict(payload or {}),
        "trace": {
            "route": list(route or []),
            "governed": True,
        },
        "compact": {
            "id": packet_id,
            "ts": timestamp,
            "src": source_node,
            "dst": target_node,
            "ch": compact_lane,
            "pri": compact_priority,
            "op": compact_op,
            "st": compact_state,
            "ref": compact_ref,
            "pl": compact_body,
            "tr": {
                "rt": list(route or []),
                "gv": 1,
            },
        },
    }


def _signal(
    *,
    signal_type: str,
    signal_class: str,
    stable_key: str,
    severity: str,
    status: str,
    data_sufficiency: str,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "signal_type": str(signal_type or "").strip().lower(),
        "signal_class": str(signal_class or "").strip().lower(),
        "stable_key": str(stable_key or "").strip().lower(),
        "severity": str(severity or "low").strip().lower(),
        "status": str(status or "observed").strip().lower(),
        "data_sufficiency": str(data_sufficiency or "partial").strip().lower(),
        "attributes": dict(attributes or {}),
    }


def _packet_intents(packets: list[dict[str, Any]]) -> list[str]:
    return _dedupe_strings(
        [str(packet.get("intent") or "").strip().lower() for packet in list(packets or [])]
    )


def _packet_metrics(
    *,
    forward_packets: list[dict[str, Any]],
    service_packets: list[dict[str, Any]],
    return_packets: list[dict[str, Any]],
) -> dict[str, Any]:
    forward = list(forward_packets or [])
    service = list(service_packets or [])
    returned = list(return_packets or [])
    return {
        "forward_packet_count": len(forward),
        "service_packet_count": len(service),
        "return_packet_count": len(returned),
        "total_packet_count": len(forward) + len(service) + len(returned),
        "forward_intents": _packet_intents(forward),
        "service_intents": _packet_intents(service),
        "return_intents": _packet_intents(returned),
    }


def _risk_level_for_feed(system_mode: str, immune_response: str) -> str:
    normalized_mode = str(system_mode or "stable").strip().lower() or "stable"
    normalized_response = str(immune_response or "ALLOW").strip().upper() or "ALLOW"
    if normalized_response in {"REJECT", "QUARANTINE"}:
        return "blocked"
    if normalized_response in {"CLAMP", "REROUTE"} and normalized_mode == "stable":
        return "caution"
    return "low" if normalized_mode == "stable" else normalized_mode


def _system_state_for_feed(
    *,
    response_mode: str,
    god_brain: dict[str, Any] | None,
    immune_response: str,
) -> dict[str, str]:
    system_mode = _state_from_posture(god_brain)
    return {
        "user_mode": str(response_mode or "fast").strip().lower() or "fast",
        "system_mode": system_mode,
        "risk_level": _risk_level_for_feed(system_mode, immune_response),
    }


def _previous_pipeline_state(previous_pipeline: dict[str, Any] | None) -> dict[str, Any]:
    previous = dict(previous_pipeline or {})
    previous_feed = dict(previous.get("realtime_signal_feed") or {})
    previous_state = dict(previous_feed.get("system_state") or {})
    if not previous_state:
        for packet in [
            *list(previous.get("forward_packets") or []),
            *list(previous.get("service_packets") or []),
            *list(previous.get("return_packets") or []),
        ]:
            state = dict(packet.get("state") or {})
            if state:
                previous_state = state
                break
    return {
        "runtime_context": _normalize_runtime_context(
            previous_feed.get("runtime_context") or previous.get("runtime_context")
        ),
        "active_lane": str(
            previous.get("active_lane") or previous_feed.get("active_lane") or DIRECT_COGNITIVE_LANE
        ).strip().lower()
        or DIRECT_COGNITIVE_LANE,
        "traffic_class": str(
            previous.get("traffic_class") or previous_feed.get("traffic_class") or "core_cognition"
        ).strip().lower()
        or "core_cognition",
        "response_mode": str(
            previous.get("response_mode") or previous_feed.get("response_mode") or "fast"
        ).strip().lower()
        or "fast",
        "contract": str(previous.get("contract") or previous_feed.get("contract") or "").strip().lower()
        or None,
        "tool_type": str(previous.get("tool_type") or previous_feed.get("tool_type") or "").strip().lower()
        or None,
        "immune_response": str(
            dict(previous.get("immune_protocol") or {}).get("response")
            or previous_feed.get("immune_response")
            or "ALLOW"
        ).strip().upper()
        or "ALLOW",
        "surface_node": str(
            previous.get("surface_node") or previous_feed.get("surface_node") or "jar"
        ).strip().lower()
        or "jar",
        "system_mode": str(previous_state.get("system_mode") or "stable").strip().lower() or "stable",
        "risk_level": str(previous_state.get("risk_level") or "low").strip().lower() or "low",
    }


def _turn_delta(
    *,
    previous_pipeline: dict[str, Any] | None,
    runtime_context: str,
    active_lane: str,
    traffic_class: str,
    response_mode: str,
    contract: str,
    tool_result: dict[str, Any] | None,
    immune_response: str,
    system_state: dict[str, str],
    surface_node: str,
) -> dict[str, Any]:
    has_previous_turn = bool(previous_pipeline)
    previous_state = _previous_pipeline_state(previous_pipeline) if has_previous_turn else {}
    tool_type = str((tool_result or {}).get("type") or "").strip().lower() or None
    delta = {
        "has_previous_turn": has_previous_turn,
        "previous_runtime_context": previous_state.get("runtime_context"),
        "previous_active_lane": previous_state.get("active_lane"),
        "previous_traffic_class": previous_state.get("traffic_class"),
        "previous_response_mode": previous_state.get("response_mode"),
        "previous_contract": previous_state.get("contract"),
        "previous_tool_type": previous_state.get("tool_type"),
        "previous_immune_response": previous_state.get("immune_response"),
        "previous_system_mode": previous_state.get("system_mode"),
        "previous_risk_level": previous_state.get("risk_level"),
        "previous_surface_node": previous_state.get("surface_node"),
        "runtime_context_changed": has_previous_turn and previous_state.get("runtime_context") != runtime_context,
        "lane_changed": has_previous_turn and previous_state.get("active_lane") != active_lane,
        "traffic_class_changed": has_previous_turn and previous_state.get("traffic_class") != traffic_class,
        "response_mode_changed": has_previous_turn and previous_state.get("response_mode") != response_mode,
        "contract_changed": has_previous_turn and previous_state.get("contract") != contract,
        "tool_changed": has_previous_turn and previous_state.get("tool_type") != tool_type,
        "immune_response_changed": has_previous_turn and previous_state.get("immune_response") != immune_response,
        "system_mode_changed": has_previous_turn and previous_state.get("system_mode") != system_state["system_mode"],
        "risk_level_changed": has_previous_turn and previous_state.get("risk_level") != system_state["risk_level"],
        "surface_node_changed": has_previous_turn and previous_state.get("surface_node") != surface_node,
    }
    delta["change_count"] = sum(
        int(bool(delta[key]))
        for key in (
            "runtime_context_changed",
            "lane_changed",
            "traffic_class_changed",
            "response_mode_changed",
            "contract_changed",
            "tool_changed",
            "immune_response_changed",
            "system_mode_changed",
            "risk_level_changed",
            "surface_node_changed",
        )
    )
    delta["stable_repeat"] = has_previous_turn and delta["change_count"] == 0
    return delta


def _severity_for_immune_response(response: str) -> str:
    normalized = str(response or "ALLOW").strip().upper() or "ALLOW"
    if normalized in {"REJECT", "QUARANTINE"}:
        return "high"
    if normalized in {"CLAMP", "REROUTE"}:
        return "medium"
    return "low"


def _build_realtime_signal_feed(
    *,
    pipeline_id: str,
    runtime_context: str,
    response_mode: str,
    contract: str,
    active_lane: str,
    traffic_class: str,
    surface_node: str,
    forward_packets: list[dict[str, Any]],
    service_packets: list[dict[str, Any]],
    return_packets: list[dict[str, Any]],
    tool_result: dict[str, Any] | None,
    god_brain: dict[str, Any] | None,
    immune_protocol: dict[str, Any] | None,
    previous_pipeline: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_context = _normalize_runtime_context(runtime_context)
    immune_response = str(
        dict(immune_protocol or {}).get("response") or "ALLOW"
    ).strip().upper() or "ALLOW"
    system_state = _system_state_for_feed(
        response_mode=response_mode,
        god_brain=god_brain,
        immune_response=immune_response,
    )
    packet_metrics = _packet_metrics(
        forward_packets=forward_packets,
        service_packets=service_packets,
        return_packets=return_packets,
    )
    delta = _turn_delta(
        previous_pipeline=previous_pipeline,
        runtime_context=normalized_context,
        active_lane=active_lane,
        traffic_class=traffic_class,
        response_mode=response_mode,
        contract=contract,
        tool_result=tool_result,
        immune_response=immune_response,
        system_state=system_state,
        surface_node=surface_node,
    )
    tool_type = str((tool_result or {}).get("type") or "").strip().lower() or None
    capability = dict((tool_result or {}).get("capability") or {})
    signals = [
        _signal(
            signal_type="runtime_boundary",
            signal_class=f"{normalized_context}_active",
            stable_key=f"runtime_boundary:{normalized_context}",
            severity="medium" if normalized_context == "operator_runtime" else "low",
            status="observed",
            data_sufficiency="sufficient",
            attributes={
                "runtime_context": normalized_context,
                "response_mode": response_mode,
                "surface_node": surface_node,
            },
        ),
        _signal(
            signal_type="lane_activity",
            signal_class="service_lane_active" if active_lane == SERVICE_TOOL_LANE else "direct_lane_active",
            stable_key=f"lane_activity:{active_lane}",
            severity="medium" if active_lane == SERVICE_TOOL_LANE else "low",
            status="observed",
            data_sufficiency="sufficient",
            attributes={
                "active_lane": active_lane,
                "traffic_class": traffic_class,
                "service_packet_count": packet_metrics["service_packet_count"],
            },
        ),
        _signal(
            signal_type="system_posture",
            signal_class=f"{system_state['system_mode']}_posture",
            stable_key=f"system_posture:{system_state['system_mode']}:{system_state['risk_level']}",
            severity="high" if system_state["risk_level"] == "blocked" else "medium" if system_state["risk_level"] in {"caution", "elevated", "degraded"} else "low",
            status="observed",
            data_sufficiency="sufficient",
            attributes={
                "system_mode": system_state["system_mode"],
                "risk_level": system_state["risk_level"],
                "immune_response": immune_response,
            },
        ),
        _signal(
            signal_type="packet_activity",
            signal_class="packet_flow_observed",
            stable_key=(
                "packet_activity:"
                f"{packet_metrics['forward_packet_count']}:"
                f"{packet_metrics['service_packet_count']}:"
                f"{packet_metrics['return_packet_count']}"
            ),
            severity="medium" if packet_metrics["service_packet_count"] else "low",
            status="observed",
            data_sufficiency="sufficient",
            attributes=packet_metrics,
        ),
        _signal(
            signal_type="turn_delta",
            signal_class=(
                "baseline_only"
                if not delta["has_previous_turn"]
                else "turn_state_stable"
                if delta["stable_repeat"]
                else "turn_shift_detected"
            ),
            stable_key=(
                "turn_delta:baseline"
                if not delta["has_previous_turn"]
                else "turn_delta:stable"
                if delta["stable_repeat"]
                else "turn_delta:shift"
            ),
            severity="medium" if delta["change_count"] else "low",
            status="delta",
            data_sufficiency="sufficient" if delta["has_previous_turn"] else "partial",
            attributes=delta,
        ),
    ]
    if tool_result:
        tool_status = str((tool_result or {}).get("status") or "completed").strip().lower() or "completed"
        signals.append(
            _signal(
                signal_type="tool_activity",
                signal_class=(
                    "service_tool_blocked"
                    if tool_status == "blocked"
                    else "service_tool_failed"
                    if tool_status == "failed"
                    else "service_tool_completed"
                ),
                stable_key=f"tool_activity:{tool_type or 'tool'}:{tool_status}",
                severity="high" if tool_status == "blocked" else "medium",
                status="observed",
                data_sufficiency="sufficient" if capability.get("module") or tool_type else "partial",
                attributes={
                    "tool_type": tool_type,
                    "tool_status": tool_status,
                    "capability_module": capability.get("module"),
                    "capability_action": capability.get("action"),
                    "provider": capability.get("provider"),
                },
            )
        )
    if immune_response != "ALLOW":
        signals.append(
            _signal(
                signal_type="immune_boundary",
                signal_class=f"immune_{immune_response.lower()}",
                stable_key=f"immune_boundary:{immune_response.lower()}",
                severity=_severity_for_immune_response(immune_response),
                status="observed",
                data_sufficiency="sufficient",
                attributes={
                    "response": immune_response,
                    "traffic_allowed": bool(dict(immune_protocol or {}).get("traffic_allowed", True)),
                    "reason_count": len(list(dict(immune_protocol or {}).get("reasons") or [])),
                    "threat_count": len(list(dict(immune_protocol or {}).get("threats") or [])),
                },
            )
        )

    realtime_signal_feed = {
        "feed_id": f"rtf_{uuid4().hex}",
        "protocol_id": REALTIME_SIGNAL_FEED_ID,
        "version": REALTIME_SIGNAL_FEED_VERSION,
        "source_pipeline_id": pipeline_id,
        "observed_at": _now_iso(),
        "runtime_context": normalized_context,
        "response_mode": response_mode,
        "contract": contract,
        "active_lane": active_lane,
        "traffic_class": traffic_class,
        "surface_node": surface_node,
        "system_state": system_state,
        "immune_response": immune_response,
        "tool_type": tool_type,
        "data_sufficiency": "sufficient",
        "packet_metrics": packet_metrics,
        "delta": delta,
        "signals": signals[:MAX_REALTIME_SIGNALS],
    }
    realtime_signal_feed["signal_count"] = len(realtime_signal_feed["signals"])
    realtime_signal_feed["validation"] = _validate_realtime_signal_feed(realtime_signal_feed)
    return realtime_signal_feed


def _validate_realtime_signal_feed(feed: dict[str, Any]) -> dict[str, bool]:
    signals = list(feed.get("signals") or [])
    packet_metrics = dict(feed.get("packet_metrics") or {})
    delta = dict(feed.get("delta") or {})
    return {
        "runtime_context_explicit": bool(str(feed.get("runtime_context") or "").strip()),
        "signal_shape_uniform": all(
            all(key in signal for key in REALTIME_SIGNAL_REQUIRED_KEYS)
            and isinstance(signal.get("attributes"), dict)
            for signal in signals
        ),
        "signal_count_bounded": len(signals) <= MAX_REALTIME_SIGNALS,
        "signal_count_matches": int(feed.get("signal_count") or 0) == len(signals),
        "stable_keys_unique": len({signal.get("stable_key") for signal in signals}) == len(signals),
        "turn_delta_present": any(signal.get("signal_type") == "turn_delta" for signal in signals),
        "delta_shape_complete": all(key in delta for key in TURN_DELTA_KEYS),
        "packet_metrics_complete": all(
            key in packet_metrics
            for key in (
                "forward_packet_count",
                "service_packet_count",
                "return_packet_count",
                "total_packet_count",
                "forward_intents",
                "service_intents",
                "return_intents",
            )
        ),
    }


def _core_forward_packets(
    *,
    response_mode: str,
    contract: str,
    god_brain: dict[str, Any] | None,
    model_route: dict[str, Any] | None,
    surface_node: str,
) -> list[dict[str, Any]]:
    priority = _priority_for_turn(response_mode, None)
    tone = _tone_for_turn(response_mode, surface_node)
    system_state = _state_from_posture(god_brain)
    route = _route_for_surface(surface_node)
    shared_state = {
        "user_mode": response_mode,
        "system_mode": system_state,
        "risk_level": "low" if system_state == "stable" else system_state,
    }
    common_constraints = ["no_tools", "bounded_reply"]
    final_constraints = list(common_constraints)
    if surface_node == "nov":
        final_constraints.append("user_facing_only")

    route_summary = str((god_brain or {}).get("strategy_label") or "governed_route")
    provider_summary = str((model_route or {}).get("label") or "local_route")

    return [
        build_pipeline_packet(
            source="llm",
            target="gb",
            lane=DIRECT_COGNITIVE_LANE,
            priority=priority,
            intent="result",
            state=shared_state,
            payload=_packet_payload(
                meaning="draft_semantic_result",
                tone=tone,
                constraints=common_constraints,
                summary="Raw model cognition entered the governed fast lane.",
                metadata={
                    "contract": contract,
                    "model_route": provider_summary,
                },
            ),
            route=route[:1],
            ref=contract,
        ),
        build_pipeline_packet(
            source="gb",
            target="jar",
            lane=DIRECT_COGNITIVE_LANE,
            priority=priority,
            intent="route",
            state=shared_state,
            payload=_packet_payload(
                meaning="governed_route_selected",
                tone=tone,
                constraints=common_constraints,
                summary="God Brain validated the lane and preserved authority.",
                metadata={
                    "contract": contract,
                    "strategy": route_summary,
                    "action_bias": (god_brain or {}).get("action_bias"),
                },
            ),
            route=route[:2],
            ref=contract,
        ),
        build_pipeline_packet(
            source="jar",
            target=surface_node,
            lane=DIRECT_COGNITIVE_LANE,
            priority=priority,
            intent="express",
            state=shared_state,
            payload=_packet_payload(
                meaning="approved_semantic_result",
                tone=tone,
                constraints=final_constraints,
                summary="Jarvis approved the meaning for the user-facing edge.",
                metadata={
                    "contract": contract,
                    "surface_node": surface_node,
                },
            ),
            route=route[:3] if surface_node == "jar" else route[:4],
            ref=contract,
        ),
    ]


def _core_return_packets(
    *,
    response_mode: str,
    contract: str,
    surface_node: str,
) -> list[dict[str, Any]]:
    priority = _priority_for_turn(response_mode, None)
    tone = _tone_for_turn(response_mode, surface_node)
    route = _return_route_for_surface(surface_node)
    shared_state = {
        "user_mode": response_mode,
        "system_mode": "stable",
        "risk_level": "low",
    }
    packets: list[dict[str, Any]] = []
    hop_pairs = list(zip(route, route[1:]))
    for index, (source, target) in enumerate(hop_pairs, start=1):
        packets.append(
            build_pipeline_packet(
                source=source,
                target=target,
                lane=DIRECT_COGNITIVE_LANE,
                priority=priority,
                intent="ack",
                state=shared_state,
                payload=_packet_payload(
                    meaning="structured_delivery_ack",
                    tone=tone,
                    constraints=["bounded_reply"],
                    summary="The direct lane returned a compact acknowledgement.",
                    metadata={
                        "contract": contract,
                        "return_hop": index,
                    },
                ),
                route=route[:index],
                ref=contract,
            )
        )
    return packets


def _service_forward_packets(
    *,
    response_mode: str,
    contract: str,
    god_brain: dict[str, Any] | None,
    surface_node: str,
) -> list[dict[str, Any]]:
    priority = _priority_for_turn(response_mode, {"type": "tool"})
    tone = _tone_for_turn(response_mode, surface_node)
    route = ["gb", "jar"] if surface_node == "jar" else ["gb", "jar", "nov"]
    shared_state = {
        "user_mode": response_mode,
        "system_mode": _state_from_posture(god_brain),
        "risk_level": "low",
    }
    packets = [
        build_pipeline_packet(
            source="gb",
            target="jar",
            lane=DIRECT_COGNITIVE_LANE,
            priority=priority,
            intent="route",
            state=shared_state,
            payload=_packet_payload(
                meaning="service_lane_selected",
                tone=tone,
                constraints=["service_lane_only", "bounded_reply"],
                summary="God Brain kept tool traffic off the fast cognition lane.",
                metadata={"contract": contract},
            ),
            route=route[:1],
            ref=contract,
        )
    ]
    if surface_node == "nov":
        packets.append(
            build_pipeline_packet(
                source="jar",
                target="nov",
                lane=DIRECT_COGNITIVE_LANE,
                priority=priority,
                intent="express",
                state=shared_state,
                payload=_packet_payload(
                    meaning="service_result_for_expression",
                    tone=tone,
                    constraints=["user_facing_only", "bounded_reply"],
                    summary="Jarvis approved the bounded service result for Nova.",
                    metadata={"contract": contract},
                ),
                route=route,
                ref=contract,
            )
        )
    return packets


def _service_return_packets(
    *,
    response_mode: str,
    contract: str,
    surface_node: str,
) -> list[dict[str, Any]]:
    priority = _priority_for_turn(response_mode, {"type": "tool"})
    tone = _tone_for_turn(response_mode, surface_node)
    route = ["jar", "gb"] if surface_node == "jar" else ["nov", "jar", "gb"]
    shared_state = {
        "user_mode": response_mode,
        "system_mode": "stable",
        "risk_level": "low",
    }
    packets: list[dict[str, Any]] = []
    for index, (source, target) in enumerate(zip(route, route[1:]), start=1):
        packets.append(
            build_pipeline_packet(
                source=source,
                target=target,
                lane=DIRECT_COGNITIVE_LANE,
                priority=priority,
                intent="ack",
                state=shared_state,
                payload=_packet_payload(
                    meaning="service_lane_ack",
                    tone=tone,
                    constraints=["bounded_reply"],
                    summary="The service-lane turn returned a structured acknowledgement.",
                    metadata={"contract": contract, "return_hop": index},
                ),
                route=route[:index],
                ref=contract,
            )
        )
    return packets


def _service_packets(
    *,
    response_mode: str,
    contract: str,
    tool_result: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    priority = _priority_for_turn(response_mode, tool_result)
    tool_type = str((tool_result or {}).get("type") or "tool").strip().lower() or "tool"
    capability = dict((tool_result or {}).get("capability") or {})
    tool_label = str(
        ((tool_result or {}).get("action") or {}).get("label")
        or (tool_result or {}).get("label")
        or tool_type
    ).strip()
    shared_state = {
        "user_mode": response_mode,
        "system_mode": "stable",
        "risk_level": "low",
    }
    service_constraints = ["service_lane_only", "no_external", "bounded_reply"]
    return [
        build_pipeline_packet(
            source="jar",
            target="svc",
            lane=SERVICE_TOOL_LANE,
            priority=priority,
            intent="tool_call",
            state=shared_state,
            payload=_packet_payload(
                meaning="governed_tool_call",
                tone="operator",
                constraints=service_constraints,
                summary="Jarvis sent bounded tool traffic to the service lane.",
                metadata={
                    "contract": contract,
                    "tool_type": tool_type,
                    "tool_label": tool_label,
                    "capability_module": capability.get("module"),
                    "capability_action": capability.get("action"),
                },
            ),
            route=["jar", "svc"],
            ref=contract,
        ),
        build_pipeline_packet(
            source="svc",
            target="jar",
            lane=SERVICE_TOOL_LANE,
            priority=priority,
            intent="tool_result",
            state=shared_state,
            payload=_packet_payload(
                meaning="bounded_tool_result",
                tone="operator",
                constraints=service_constraints,
                summary="The service lane returned structured tool output to Jarvis.",
                metadata={
                    "contract": contract,
                    "tool_type": tool_type,
                    "capability_module": capability.get("module"),
                    "capability_action": capability.get("action"),
                    "provider": capability.get("provider"),
                    "error_type": capability.get("error_type"),
                },
            ),
            route=["jar", "svc", "jar"],
            ref=contract,
        ),
    ]


def build_governed_turn_pipeline(
    *,
    response_mode: str,
    contract: str | None = None,
    god_brain: dict[str, Any] | None = None,
    model_route: dict[str, Any] | None = None,
    tool_result: dict[str, Any] | None = None,
    surface_identity: str | None = None,
    turn_contract: dict[str, Any] | None = None,
    runtime_context: str = "live_runtime",
    previous_pipeline: dict[str, Any] | None = None,
    operator_text: str | None = None,
    cloud_forge_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the governed direct pipeline trace for one turn."""
    normalized_mode = str(response_mode or "fast").strip().lower() or "fast"
    normalized_runtime_context = _normalize_runtime_context(runtime_context)

    from src.operator_cognition_coherence_fabric import (
        build_coherence_fabric_status,
        evaluate_attestation_coherence,
        evaluate_pipeline_coherence,
    )

    coherence_status = build_coherence_fabric_status()
    safety_modes = coherence_status.get("envelope_governance_modes") or []
    safety_halt = any(
        isinstance(item, dict)
        and item.get("envelope_id") == "safety_envelope"
        and str(item.get("governance_mode") or "").lower() == "halt"
        for item in safety_modes
    )
    coherence_eval = evaluate_pipeline_coherence(
        fabric_genes_aligned=bool(coherence_status.get("fabric_genes_aligned")),
        safety_halt=safety_halt,
    )
    coherence_protocol = {"response": "ALLOW"}
    if not coherence_eval.allowed:
        coherence_protocol = {
            "response": "BLOCK",
            "reason": coherence_eval.reason or "coherence fabric blocked",
        }
    else:
        attestation_eval = evaluate_attestation_coherence()
        if not attestation_eval.allowed:
            coherence_protocol = {
                "response": "BLOCK",
                "reason": attestation_eval.reason or "linguistic attestation blocked",
            }

    active_contract = str(contract or (turn_contract or {}).get("contract_label") or "direct_answer").strip()
    surface_node = _surface_node(surface_identity or (god_brain or {}).get("surface_identity"), normalized_mode)
    if tool_result:
        direct_route = ["gb", "jar"] if surface_node == "jar" else ["gb", "jar", "nov"]
        return_route = ["jar", "gb"] if surface_node == "jar" else ["nov", "jar", "gb"]
        forward_packets = _service_forward_packets(
            response_mode=normalized_mode,
            contract=active_contract,
            god_brain=god_brain,
            surface_node=surface_node,
        )
        return_packets = _service_return_packets(
            response_mode=normalized_mode,
            contract=active_contract,
            surface_node=surface_node,
        )
        service_packets = _service_packets(
            response_mode=normalized_mode,
            contract=active_contract,
            tool_result=tool_result,
        )
        summary = "God Brain and Jarvis kept tool traffic on the slower governed service lane."
        active_lane = SERVICE_TOOL_LANE
        traffic_class = "service"
    else:
        direct_route = _route_for_surface(surface_node)
        return_route = _return_route_for_surface(surface_node)
        forward_packets = _core_forward_packets(
            response_mode=normalized_mode,
            contract=active_contract,
            god_brain=god_brain,
            model_route=model_route,
            surface_node=surface_node,
        )
        return_packets = _core_return_packets(
            response_mode=normalized_mode,
            contract=active_contract,
            surface_node=surface_node,
        )
        service_packets = []
        summary = "LLM, God Brain, Jarvis, and the expression edge stayed on the governed direct lane."
        active_lane = DIRECT_COGNITIVE_LANE
        traffic_class = "core_cognition"

    immune_evaluation = apply_immune_protocol(
        forward_packets=forward_packets,
        service_packets=service_packets,
        return_packets=return_packets,
        active_lane=active_lane,
        direct_route=direct_route,
    )
    forward_packets = immune_evaluation["forward_packets"]
    service_packets = immune_evaluation["service_packets"]
    return_packets = immune_evaluation["return_packets"]
    immune_protocol = immune_evaluation["immune_protocol"]
    if coherence_protocol["response"] != "ALLOW":
        summary = f"{summary} Coherence response: {coherence_protocol['response']}."
    if immune_protocol["response"] != "ALLOW":
        summary = f"{summary} Immune response: {immune_protocol['response']}."
    pipeline_id = f"gdp_{uuid4().hex}"
    realtime_signal_feed = _build_realtime_signal_feed(
        pipeline_id=pipeline_id,
        runtime_context=normalized_runtime_context,
        response_mode=normalized_mode,
        contract=active_contract,
        active_lane=active_lane,
        traffic_class=traffic_class,
        surface_node=surface_node,
        forward_packets=forward_packets,
        service_packets=service_packets,
        return_packets=return_packets,
        tool_result=tool_result,
        god_brain=god_brain,
        immune_protocol=immune_protocol,
        previous_pipeline=previous_pipeline,
    )
    from src.realtime_event_cause_predictor import (
        interpret_realtime_signal_feed,
        validate_interpreted_event_state,
    )
    from src.governed_event_chain import (
        governed_event,
        validate_governed_event_result,
    )
    from src.operator_health_sentinel import (
        observe_operator_health,
        validate_operator_health_snapshot,
    )

    realtime_event_cause_predictor = interpret_realtime_signal_feed(
        realtime_signal_feed,
        runtime_context=normalized_runtime_context,
    )
    governed_event_guard = governed_event(
        realtime_signal_feed,
        prediction=realtime_event_cause_predictor,
        runtime_context=normalized_runtime_context,
    )
    operator_health_sentinel = observe_operator_health(
        {
            "runtime_context": normalized_runtime_context,
            "realtime_signal_feed": realtime_signal_feed,
            "realtime_event_cause_predictor": realtime_event_cause_predictor,
            "governed_event": governed_event_guard,
        },
        runtime_context=normalized_runtime_context,
        operator_text=operator_text,
        previous_pipeline=previous_pipeline,
    )
    from src.cognitive_bridge import route_to_bridge
    from src.jarvis_detachment_guard import build_bridge_attestation

    bridge_hops = []
    if god_brain:
        bridge_hops.append(
            route_to_bridge(
                {
                    "source": "swarm",
                    "type": "deliberation_request",
                    "payload": {
                        "pipeline_id": pipeline_id,
                        "strategy_label": (god_brain or {}).get("strategy_label"),
                        "action_bias": (god_brain or {}).get("action_bias"),
                        "contract": active_contract,
                        "intent": (
                            (god_brain or {}).get("strategy_label")
                            or active_contract
                            or "governed_direct_pipeline_deliberation"
                        ),
                        "execution_intent": "route",
                        "bridge_attestation": build_bridge_attestation(
                            ingress="governed_direct_pipeline",
                            surface="swarm_deliberation",
                            source_id=pipeline_id,
                            route="governed_direct_pipeline.swarm_deliberation",
                            intent="route",
                            runtime_context=normalized_runtime_context,
                            packet_type="deliberation_request",
                        ),
                    },
                    "requires_approval": False,
                    "risk": "medium" if active_lane == SERVICE_TOOL_LANE else "low",
                },
                runtime_context=normalized_runtime_context,
            )
        )
    bridge_hops.append(
        route_to_bridge(
            {
                "source": "service_lane" if tool_result else "llm",
                "type": "tool_result_observation" if tool_result else "generation_request",
                "payload": {
                    "pipeline_id": pipeline_id,
                    "contract": active_contract,
                    "response_mode": normalized_mode,
                    "tool_type": (tool_result or {}).get("type"),
                    "route_id": (model_route or {}).get("id"),
                    "execution_intent": "observe" if tool_result else "respond",
                    "bridge_attestation": build_bridge_attestation(
                        ingress="governed_direct_pipeline",
                        surface="service_observation" if tool_result else "llm_generation",
                        source_id=pipeline_id,
                        route="governed_direct_pipeline.service_observation" if tool_result else "governed_direct_pipeline.llm_generation",
                        intent="observe" if tool_result else "respond",
                        runtime_context=normalized_runtime_context,
                        packet_type="tool_result_observation" if tool_result else "generation_request",
                    ),
                },
                "requires_approval": False,
                "risk": "medium" if tool_result else "low",
            },
            runtime_context=normalized_runtime_context,
        )
    )
    bridge_hops.append(
        route_to_bridge(
            {
                "source": "predictor",
                "type": "signal_evaluation",
                "payload": {
                    "pipeline_id": pipeline_id,
                    "active_lane": active_lane,
                    "traffic_class": traffic_class,
                    "signal_count": realtime_signal_feed.get("signal_count"),
                    "execution_intent": "observe",
                    "bridge_attestation": build_bridge_attestation(
                        ingress="governed_direct_pipeline",
                        surface="predictor_signal",
                        source_id=pipeline_id,
                        route="governed_direct_pipeline.predictor_signal",
                        intent="observe",
                        runtime_context=normalized_runtime_context,
                        packet_type="signal_evaluation",
                    ),
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context=normalized_runtime_context,
        )
    )

    pipeline = {
        "pipeline_id": pipeline_id,
        "protocol_id": PIPELINE_ID,
        "version": PIPELINE_VERSION,
        "name": "Governed Direct Pipeline",
        "doctrine": (
            "AAIS is the spine. Core cognition stays on the governed direct lane while "
            "tool traffic remains on the slower service lane."
        ),
        "summary": summary,
        "contract": active_contract,
        "response_mode": normalized_mode,
        "runtime_context": normalized_runtime_context,
        "active_lane": active_lane,
        "traffic_class": traffic_class,
        "surface_identity": str(surface_identity or (god_brain or {}).get("surface_identity") or "jarvis").strip() or "jarvis",
        "surface_node": surface_node,
        "direct_route": direct_route,
        "return_route": return_route,
        "forward_packets": forward_packets,
        "service_packets": service_packets,
        "return_packets": return_packets,
        "immune_protocol": immune_protocol,
        "coherence_protocol": coherence_protocol,
        "bridge_hops": bridge_hops,
        "realtime_signal_feed": realtime_signal_feed,
        "realtime_event_cause_predictor": realtime_event_cause_predictor,
        "governed_event": governed_event_guard,
        "operator_health_sentinel": operator_health_sentinel,
        "validation": {
            "uniform_packet_shape": all(
                all(
                    key in packet
                    for key in ("packet_id", "timestamp", "source", "target", "lane", "priority", "intent", "state", "payload", "trace", "compact")
                )
                for packet in [*forward_packets, *service_packets, *return_packets]
            ),
            "god_brain_in_path": any(packet["source"] == "gb" or packet["target"] == "gb" for packet in [*forward_packets, *return_packets]),
            "jarvis_authority_preserved": any(packet["source"] == "jar" for packet in [*forward_packets, *service_packets]),
            "tool_traffic_isolated": all(packet["lane"] == SERVICE_TOOL_LANE for packet in service_packets),
            "direct_lane_tool_free": all(
                packet["intent"] not in {"tool_call", "tool_result"}
                for packet in [*forward_packets, *return_packets]
            ),
            "immune_traffic_allowed": immune_protocol["traffic_allowed"],
            "realtime_signal_feed_valid": all(
                ok for ok in realtime_signal_feed["validation"].values() if isinstance(ok, bool)
            ),
            "realtime_event_cause_predictor_valid": all(
                ok
                for ok in validate_interpreted_event_state(
                    realtime_event_cause_predictor
                ).values()
                if isinstance(ok, bool)
            ),
            "governed_event_valid": all(
                ok
                for ok in validate_governed_event_result(
                    governed_event_guard
                ).values()
                if isinstance(ok, bool)
            ),
            "operator_health_sentinel_valid": all(
                ok
                for ok in validate_operator_health_snapshot(
                    operator_health_sentinel
                ).values()
                if isinstance(ok, bool)
            ),
            "bridge_hops_routed": all(
                hop.get("decision") in {"ALLOW", "DEGRADE"}
                for hop in bridge_hops
            ),
        },
        "model_route": {
            "id": (model_route or {}).get("id"),
            "label": (model_route or {}).get("label"),
        },
        "tool_type": (tool_result or {}).get("type"),
        "capability": dict((tool_result or {}).get("capability") or {}) or None,
    }
    pipeline["continuity_witness_input"] = build_continuity_witness_input(pipeline)
    if cloud_forge_context:
        from src.cloud_forge.rails import attach_cloud_forge_to_pipeline

        pipeline = attach_cloud_forge_to_pipeline(pipeline, cloud_forge_context)
    from src.aais_ul_substrate import wrap_pipeline

    return wrap_pipeline(pipeline)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def to_pipeline_envelope(
    pipeline: dict[str, Any],
    *,
    cisiv_stage: str = "implementation",
    claim_label: str = "asserted",
) -> dict[str, Any]:
    """Map a governed turn pipeline trace to governed_direct_pipeline.v1."""
    now = _utc_now_iso()
    active_lane = str(pipeline.get("active_lane") or DIRECT_COGNITIVE_LANE)
    lanes = [
        {
            "lane_name": DIRECT_COGNITIVE_LANE,
            "compact_channel": _compact_channel_for_lane(DIRECT_COGNITIVE_LANE),
            "claim_label": claim_label,
        },
        {
            "lane_name": SERVICE_TOOL_LANE,
            "compact_channel": _compact_channel_for_lane(SERVICE_TOOL_LANE),
            "claim_label": claim_label,
        },
    ]
    packets = []
    for packet in [
        *(pipeline.get("forward_packets") or []),
        *(pipeline.get("service_packets") or []),
        *(pipeline.get("return_packets") or []),
    ]:
        if not isinstance(packet, dict):
            continue
        state_value = packet.get("state")
        if isinstance(state_value, dict):
            state_code = int(state_value.get("code") or 0)
        elif isinstance(state_value, (int, float)):
            state_code = int(state_value)
        else:
            state_code = STATE_CODES.get(str(state_value or "").strip().lower(), 0)
        packets.append(
            {
                "packet_id": str(packet.get("packet_id") or ""),
                "lane_name": str(packet.get("lane") or active_lane),
                "operation": str(packet.get("intent") or ""),
                "source_node": _node_label(str(packet.get("source") or "")),
                "target_node": _node_label(str(packet.get("target") or "")),
                "priority": str(packet.get("priority") or "normal"),
                "state_code": state_code,
                "intent": str(packet.get("intent") or ""),
                "claim_label": claim_label,
            }
        )
    feed = dict(pipeline.get("realtime_signal_feed") or {})
    immune = dict(pipeline.get("immune_protocol") or {})
    coherence = dict(pipeline.get("coherence_protocol") or {})
    coherence_response = str(coherence.get("response") or "ALLOW").strip().upper()
    if coherence_response not in {"ALLOW", "BLOCK"}:
        coherence_response = "ALLOW"
    coherence_reason = str(coherence.get("reason") or "").strip()[:160]
    risk = str(feed.get("risk_level") or "low").strip().lower()
    if risk not in {"low", "medium", "high", "critical"}:
        risk = "medium"
    signal_feed = {
        "feed_id": str(feed.get("feed_id") or pipeline.get("pipeline_id") or ""),
        "risk_level": risk,
        "system_state": str(feed.get("system_state") or pipeline.get("traffic_class") or ""),
        "immune_response": str(immune.get("response") or "ALLOW"),
        "coherence_response": coherence_response,
        "coherence_reason": coherence_reason,
        "claim_label": claim_label,
    }
    return {
        "governed_direct_pipeline_version": "governed_direct_pipeline.v1",
        "pipeline_id": str(pipeline.get("pipeline_id") or PIPELINE_ID),
        "pipeline_version": str(pipeline.get("version") or PIPELINE_VERSION),
        "turn_id": str(pipeline.get("pipeline_id") or ""),
        "lanes": lanes,
        "packets": packets,
        "signal_feed": signal_feed,
        "cisiv_stage": cisiv_stage,
        "claim_label": claim_label,
        "created_at_utc": now,
        "updated_at_utc": now,
    }
