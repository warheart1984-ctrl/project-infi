"""Shared RLS validation helpers for bridge, ingress, and checkpoint validators."""

from __future__ import annotations

from typing import Any

from src.rls.adapters import from_reasoning_exchange_packet
from src.rls.falsity_registry import FalsityRegistry
from src.rls.substrate import (
    evaluate_missing_verdict,
    evaluate_reasoning_graph,
    rls_allows_escalation,
    rls_mode_for_level,
)


def rls_ingress_applies(normalized_packet: dict[str, Any]) -> bool:
    """Whether RLS should run for this normalized bridge packet."""
    packet_type = str(normalized_packet.get("type") or "").strip()
    if packet_type == "reasoning_packet_ingress":
        return True
    if packet_type in {"generation_request", "deliberation_request"}:
        fields = _ingress_payload_fields(normalized_packet)
        return bool(fields["claim"] or fields["reasoning"])
    return False


def _ingress_payload_fields(normalized_packet: dict[str, Any]) -> dict[str, Any]:
    payload = dict(normalized_packet.get("payload") or {})
    return {
        "claim": str(payload.get("claim") or "").strip(),
        "reasoning": str(payload.get("reasoning") or "").strip(),
        "evidence": list(payload.get("evidence") or []),
        "confidence": payload.get("confidence"),
        "packet_id": payload.get("packet_id") or normalized_packet.get("id"),
    }


def evaluate_exchange_packet_rls(
    packet: dict[str, Any],
    *,
    record_quarantine: bool = True,
    otem_level: int | None = None,
    registry: FalsityRegistry | None = None,
) -> dict[str, Any]:
    """Evaluate RLS for a normalized reasoning exchange packet."""
    graph = from_reasoning_exchange_packet(packet)
    return evaluate_reasoning_graph(
        graph,
        otem_level=otem_level,
        record_quarantine=record_quarantine,
        registry=registry,
    )


def evaluate_bridge_ingress_rls(
    normalized_packet: dict[str, Any],
    governance_packet: dict[str, Any] | None = None,
    *,
    record_quarantine: bool = True,
    otem_level: int | None = None,
) -> dict[str, Any]:
    """Evaluate RLS for a cognitive bridge reasoning_packet_ingress payload."""
    fields = _ingress_payload_fields(normalized_packet)
    if not fields["claim"] and not fields["reasoning"]:
        return evaluate_missing_verdict(otem_level)

    packet = {
        "id": fields.get("packet_id"),
        "payload": {
            "claim": fields["claim"],
            "reasoning": fields["reasoning"],
            "evidence": fields["evidence"],
            "confidence": fields["confidence"],
        },
        "meta": {
            "source": str((governance_packet or {}).get("source") or "external"),
        },
    }
    return evaluate_exchange_packet_rls(
        packet,
        record_quarantine=record_quarantine,
        otem_level=otem_level,
    )


def validate_rls_admissible(
    normalized_packet: dict[str, Any],
    governance_packet: dict[str, Any] | None = None,
    *,
    bridge_result: dict[str, Any] | None = None,
    envelope: dict[str, Any] | None = None,
    otem_level: int | None = None,
    record_quarantine: bool = False,
) -> dict[str, Any]:
    """
    Run RLS admissibility check for ingress/checkpoint validators.

    Returns an outcome dict with ``allows``, ``status``, ``rls_verdict``, and summary fields.
    """
    if not rls_ingress_applies(normalized_packet):
        return {
            "allows": True,
            "status": "skipped",
            "summary": "RLS ingress does not apply to this packet type.",
            "rls_verdict": None,
            "allows_escalation": True,
            "reason_codes": [],
        }

    verdict = None
    if envelope:
        verdict = envelope.get("rls_verdict")
    if not verdict and bridge_result:
        verdict = bridge_result.get("rls_verdict")
    if not verdict:
        verdict = evaluate_bridge_ingress_rls(
            normalized_packet,
            governance_packet,
            record_quarantine=record_quarantine,
            otem_level=otem_level,
        )

    allows_ingress = str(verdict.get("verdict")) != "reject"
    allows_escalation = rls_allows_escalation(verdict, otem_level=otem_level)
    mode = str(verdict.get("mode") or rls_mode_for_level(otem_level))
    violations = list(verdict.get("violations") or [])
    violation_codes = [str(v.get("code")) for v in violations if v.get("code")]

    if allows_ingress:
        summary = f"RLS {verdict.get('verdict')} in {mode} mode."
    else:
        summary = (
            "RLS rejected reasoning graph"
            + (f" ({', '.join(violation_codes[:3])})" if violation_codes else "")
            + "."
        )

    return {
        "allows": allows_ingress,
        "status": "pass" if allows_ingress else "fail",
        "summary": summary,
        "rls_verdict": verdict,
        "allows_escalation": allows_escalation,
        "reason_codes": violation_codes,
    }
