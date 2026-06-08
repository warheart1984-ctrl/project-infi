"""AAIS immune protocol for governed packet traffic.

The immune protocol sits alongside the lane governor and inspects packet
traffic for anomalies or violations before traffic is considered safe. It can
allow, clamp, reroute, reject, or quarantine traffic while returning a compact
audit object for the runtime trace.
"""

from __future__ import annotations

from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any

from src.seam_log import record_seam_event


IMMUNE_PROTOCOL_ID = "aais.immune_protocol"
IMMUNE_PROTOCOL_VERSION = "1.0"

DIRECT_COGNITIVE_LANE = "direct_cognitive"
SERVICE_TOOL_LANE = "service_tools"

PACKET_REQUIRED_KEYS = (
    "packet_id",
    "timestamp",
    "source",
    "target",
    "lane",
    "priority",
    "intent",
    "state",
    "payload",
    "trace",
    "compact",
)

DIRECT_TOOL_INTENTS = {"tool_call", "tool_result"}
MEMORY_LEAK_KEYS = {
    "memory_write",
    "memory_mutation",
    "canonical_memory_write",
    "persistent_memory",
    "session_transcript",
    "context_dump",
    "full_context",
}

MAX_DIRECT_SUMMARY_CHARS = 180


class ImmuneResponse(str, Enum):
    ALLOW = "ALLOW"
    CLAMP = "CLAMP"
    REROUTE = "REROUTE"
    REJECT = "REJECT"
    QUARANTINE = "QUARANTINE"


RESPONSE_ORDER = {
    ImmuneResponse.ALLOW: 0,
    ImmuneResponse.CLAMP: 1,
    ImmuneResponse.REROUTE: 2,
    ImmuneResponse.REJECT: 3,
    ImmuneResponse.QUARANTINE: 4,
}


def _clip_text(value: Any, *, limit: int = MAX_DIRECT_SUMMARY_CHARS) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _raise_response(current: ImmuneResponse, next_response: ImmuneResponse) -> ImmuneResponse:
    if RESPONSE_ORDER[next_response] > RESPONSE_ORDER[current]:
        return next_response
    return current


def _classification_for_response(response: ImmuneResponse) -> str:
    if response == ImmuneResponse.ALLOW:
        return "normal"
    if response in {ImmuneResponse.CLAMP, ImmuneResponse.REROUTE}:
        return "anomaly"
    return "violation"


def _lane_channel(lane: str) -> str:
    return "svc" if lane == SERVICE_TOOL_LANE else "core"


def _mark_packet_lane(packet: dict[str, Any], lane: str) -> None:
    packet["lane"] = lane
    compact = packet.get("compact")
    if isinstance(compact, dict):
        compact["ch"] = _lane_channel(lane)
        trace = compact.get("tr")
        if isinstance(trace, dict):
            trace["im"] = 1
    trace = packet.get("trace")
    if isinstance(trace, dict):
        trace["immune_rerouted"] = True
    payload = packet.get("payload")
    if isinstance(payload, dict):
        metadata = payload.setdefault("metadata", {})
        if isinstance(metadata, dict):
            metadata["immune_response"] = ImmuneResponse.REROUTE.value


def _has_truthy_value(value: Any) -> bool:
    if value in (None, False, "", [], (), {}):
        return False
    return True


def apply_immune_protocol(
    *,
    forward_packets: list[dict[str, Any]],
    service_packets: list[dict[str, Any]],
    return_packets: list[dict[str, Any]],
    active_lane: str,
    direct_route: list[str] | None = None,
    runtime_dir: str | Path | None = None,
    hardening_profile: Any | None = None,
) -> dict[str, Any]:
    """Inspect and adapt governed packet traffic before it is surfaced."""

    forward = [deepcopy(packet) for packet in forward_packets or []]
    service = [deepcopy(packet) for packet in service_packets or []]
    returned = [deepcopy(packet) for packet in return_packets or []]
    response = ImmuneResponse.ALLOW
    reasons: list[str] = []
    threats: list[dict[str, Any]] = []
    clamped_packet_ids: list[str] = []
    rerouted_packet_ids: list[str] = []
    rejected_packet_ids: list[str] = []
    quarantined_nodes: list[str] = []
    threat_memory_hits: list[str] = []
    summary_limit = MAX_DIRECT_SUMMARY_CHARS
    hardening_generation = 0
    if hardening_profile is not None:
        hardening_generation = int(getattr(hardening_profile, "defense_generation", 0) or 0)
        summary_limit = int(
            getattr(hardening_profile, "summary_char_limit", lambda: MAX_DIRECT_SUMMARY_CHARS)()
            if callable(getattr(hardening_profile, "summary_char_limit", None))
            else MAX_DIRECT_SUMMARY_CHARS
        )

    def record_threat(
        *,
        code: str,
        packet_id: str | None,
        message: str,
        next_response: ImmuneResponse,
    ) -> None:
        nonlocal response
        if hardening_profile is not None:
            floor = hardening_profile.min_floor_for_code(code)
            if RESPONSE_ORDER[floor] > RESPONSE_ORDER[next_response]:
                next_response = floor
                message = f"{message} Hardening floor raised response to {floor.value}."
                threat_memory_hits.append(code)
        response = _raise_response(response, next_response)
        reasons.append(message)
        threat = {
            "code": code,
            "packet_id": packet_id,
            "message": message,
            "classification": _classification_for_response(next_response),
            "response": next_response.value,
        }
        threats.append(threat)
        record_seam_event(
            classification="anomaly"
            if threat["classification"] == "anomaly"
            else "boundary_violation",
            source=IMMUNE_PROTOCOL_ID,
            boundary="governed_packet_boundary",
            severity="medium" if next_response in {ImmuneResponse.CLAMP, ImmuneResponse.REROUTE} else "high",
            decision=next_response.value,
            component_id=IMMUNE_PROTOCOL_ID,
            runtime_context=active_lane,
            event_type="immune_packet_threat",
            reason=message,
            details={
                "code": code,
                "packet_id": packet_id,
                "classification": threat["classification"],
                "active_lane": active_lane,
            },
            runtime_dir=runtime_dir,
        )

    all_packets = [*forward, *service, *returned]
    for packet in all_packets:
        packet_id = str(packet.get("packet_id") or "").strip() or None
        missing = [key for key in PACKET_REQUIRED_KEYS if key not in packet]
        if missing:
            rejected_packet_ids.append(packet_id or "unknown")
            record_threat(
                code="invalid_packet_structure",
                packet_id=packet_id,
                message=f"{packet_id or 'packet'} is missing required fields: {', '.join(missing)}.",
                next_response=ImmuneResponse.REJECT,
            )
            continue
        if not isinstance(packet.get("payload"), dict) or not isinstance(packet.get("trace"), dict) or not isinstance(packet.get("compact"), dict):
            rejected_packet_ids.append(packet_id or "unknown")
            record_threat(
                code="invalid_packet_shape",
                packet_id=packet_id,
                message=f"{packet_id or 'packet'} must preserve dict payload, trace, and compact sections.",
                next_response=ImmuneResponse.REJECT,
            )

    for packet in [*forward, *returned]:
        if not isinstance(packet.get("payload"), dict):
            continue
        if str(packet.get("lane") or "").strip().lower() != DIRECT_COGNITIVE_LANE:
            continue
        summary = packet["payload"].get("summary")
        if summary and len(" ".join(str(summary).split()).strip()) > summary_limit:
            packet["payload"]["summary"] = _clip_text(summary, limit=summary_limit)
            metadata = packet["payload"].setdefault("metadata", {})
            if isinstance(metadata, dict):
                metadata["immune_clamped"] = True
                metadata["immune_clamp_reason"] = "packet_bloat"
            clamped_packet_ids.append(str(packet.get("packet_id") or "unknown"))
            record_threat(
                code="packet_bloat",
                packet_id=str(packet.get("packet_id") or "") or None,
                message=f"{packet.get('packet_id') or 'packet'} exceeded fast-lane summary limits and was clamped.",
                next_response=ImmuneResponse.CLAMP,
            )

    def reroute_tool_bleed(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        kept: list[dict[str, Any]] = []
        for packet in packets:
            intent = str(packet.get("intent") or "").strip().lower()
            lane = str(packet.get("lane") or "").strip().lower()
            packet_id = str(packet.get("packet_id") or "").strip() or None
            if intent in DIRECT_TOOL_INTENTS and lane != SERVICE_TOOL_LANE:
                _mark_packet_lane(packet, SERVICE_TOOL_LANE)
                service.append(packet)
                rerouted_packet_ids.append(packet_id or "unknown")
                record_threat(
                    code="tool_bleed_into_core_lane",
                    packet_id=packet_id,
                    message=f"{packet_id or 'packet'} carried tool traffic on the core lane and was rerouted.",
                    next_response=ImmuneResponse.REROUTE,
                )
                continue
            kept.append(packet)
        return kept

    forward = reroute_tool_bleed(forward)
    returned = reroute_tool_bleed(returned)

    nodes_in_path = {
        str(node).strip().lower()
        for node in [
            *(direct_route or []),
            *[packet.get("source") for packet in [*forward, *service, *returned]],
            *[packet.get("target") for packet in [*forward, *service, *returned]],
        ]
        if str(node or "").strip()
    }
    missing_core_nodes = [node for node in ("gb", "jar") if node not in nodes_in_path]
    if missing_core_nodes:
        quarantined_nodes.extend(missing_core_nodes)
        record_threat(
            code="authority_bypass_attempt",
            packet_id=None,
            message=(
                "Governed traffic attempted to bypass "
                f"{' and '.join(node.upper() for node in missing_core_nodes)} and was quarantined."
            ),
            next_response=ImmuneResponse.QUARANTINE,
        )

    for packet in [*forward, *returned]:
        if str(packet.get("lane") or "").strip().lower() != DIRECT_COGNITIVE_LANE:
            continue
        payload = packet.get("payload")
        if not isinstance(payload, dict):
            continue
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            continue
        leaking_keys = sorted(key for key in MEMORY_LEAK_KEYS if _has_truthy_value(metadata.get(key)))
        if leaking_keys:
            packet_id = str(packet.get("packet_id") or "").strip() or None
            rejected_packet_ids.append(packet_id or "unknown")
            record_threat(
                code="memory_context_leak",
                packet_id=packet_id,
                message=(
                    f"{packet_id or 'packet'} attempted to carry memory/context mutation keys "
                    f"on the core lane: {', '.join(leaking_keys)}."
                ),
                next_response=ImmuneResponse.REJECT,
            )

    rejected_ids = set(rejected_packet_ids)
    if response in {ImmuneResponse.REJECT, ImmuneResponse.QUARANTINE}:
        if response == ImmuneResponse.QUARANTINE:
            forward = []
            returned = []
            service = []
        else:
            forward = [
                packet
                for packet in forward
                if str(packet.get("packet_id") or "unknown") not in rejected_ids
            ]
            returned = [
                packet
                for packet in returned
                if str(packet.get("packet_id") or "unknown") not in rejected_ids
            ]

    immune_protocol = {
        "protocol_id": IMMUNE_PROTOCOL_ID,
        "version": IMMUNE_PROTOCOL_VERSION,
        "doctrine": (
            "The AAIS Immune Protocol inspects governed packet traffic, classifies anomalies or "
            "violations, and applies corrective actions before traffic is considered safe."
        ),
        "defensive_only": True,
        "classification": _classification_for_response(response),
        "response": response.value,
        "traffic_allowed": response not in {ImmuneResponse.REJECT, ImmuneResponse.QUARANTINE},
        "reasons": reasons[:24],
        "threats": threats[:24],
        "hardening_generation": hardening_generation,
        "threat_memory_hits": sorted(set(threat_memory_hits)),
        "summary_char_limit": summary_limit,
        "stats": {
            "inspected_packets": len(all_packets),
            "clamped_packets": len(clamped_packet_ids),
            "rerouted_packets": len(rerouted_packet_ids),
            "rejected_packets": len(rejected_packet_ids),
            "quarantined_nodes": len(set(quarantined_nodes)),
        },
        "mutations": {
            "clamped_packet_ids": sorted(set(clamped_packet_ids)),
            "rerouted_packet_ids": sorted(set(rerouted_packet_ids)),
            "rejected_packet_ids": sorted(set(rejected_packet_ids)),
            "quarantined_nodes": sorted(set(quarantined_nodes)),
        },
        "observed_lane": str(active_lane or DIRECT_COGNITIVE_LANE).strip().lower() or DIRECT_COGNITIVE_LANE,
    }

    return {
        "forward_packets": forward,
        "service_packets": service,
        "return_packets": returned,
        "immune_protocol": immune_protocol,
    }


def apply_predictor_bounded_escalation(
    immune_protocol: dict[str, Any],
    *,
    confidence: float,
    severity: float,
    session_id: str = "global",
) -> dict[str, Any]:
    """Policy-bound predictor escalation capped at CLAMP/REROUTE (Release 33)."""
    from src.immune_policy_enrollment import (
        evaluate_predictor_bounded_escalation,
        record_predictor_escalation_incident,
    )

    current = str(immune_protocol.get("response") or "ALLOW").upper()
    if current in {"REJECT", "QUARANTINE"}:
        return immune_protocol
    requested = "ALLOW"
    if confidence >= 0.7:
        requested = "CLAMP"
    elif severity >= 0.8:
        requested = "REROUTE"
    if requested == "ALLOW":
        return immune_protocol
    decision = evaluate_predictor_bounded_escalation(
        confidence=confidence,
        severity=severity,
        requested_response=requested,
    )
    if not decision.get("allowed"):
        return immune_protocol
    updated = dict(immune_protocol)
    updated["response"] = decision["response"]
    updated["traffic_allowed"] = decision["response"] not in {"REJECT", "QUARANTINE"}
    updated["predictor_bounded_escalation"] = decision
    record_predictor_escalation_incident(session_id=session_id, escalation=decision)
    return updated
