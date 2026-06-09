"""Shared Wonder validation helpers for bridge and ingress validators."""

from __future__ import annotations

from typing import Any

from src.wonder.adapters import extract_conceptual_text_from_bridge_packet
from src.wonder.gate import (
    evaluate_conceptual_possibility,
    sandbox_blocks_at_mode,
    wonder_mode_for_level,
)

WONDER_PACKET_TYPES = frozenset(
    {"generation_request", "deliberation_request", "reasoning_packet_ingress"}
)


def wonder_ingress_applies(normalized_packet: dict[str, Any]) -> bool:
    """Whether Wonder should run for this normalized bridge packet."""
    packet_type = str(normalized_packet.get("type") or "").strip()
    return packet_type in WONDER_PACKET_TYPES


def evaluate_bridge_ingress_wonder(
    normalized_packet: dict[str, Any],
    governance_packet: dict[str, Any] | None = None,
    *,
    otem_level: int | None = None,
) -> dict[str, Any]:
    """Evaluate Wonder for a cognitive bridge imagination-bearing packet."""
    possibility = extract_conceptual_text_from_bridge_packet(normalized_packet)
    return evaluate_conceptual_possibility(possibility, otem_level=otem_level)


def validate_wonder_permitted(
    normalized_packet: dict[str, Any],
    governance_packet: dict[str, Any] | None = None,
    *,
    bridge_result: dict[str, Any] | None = None,
    otem_level: int | None = None,
) -> dict[str, Any]:
    """
    Run Wonder admissibility check for ingress validators.

    Returns an outcome dict with ``allows``, ``status``, ``wonder_verdict``, and summary fields.
    """
    if not wonder_ingress_applies(normalized_packet):
        return {
            "allows": True,
            "status": "skipped",
            "summary": "Wonder ingress does not apply to this packet type.",
            "wonder_verdict": None,
            "reason_codes": [],
        }

    verdict = None
    if bridge_result:
        verdict = bridge_result.get("wonder_verdict")
    if not verdict:
        verdict = evaluate_bridge_ingress_wonder(
            normalized_packet,
            governance_packet,
            otem_level=otem_level,
        )

    v = str(verdict.get("verdict") or "permit")
    mode = str(verdict.get("mode") or wonder_mode_for_level(otem_level))
    violations = list(verdict.get("violations") or [])
    violation_codes = [str(vv.get("code")) for vv in violations if vv.get("code")]

    blocks = v == "forbid" or (v == "sandbox" and sandbox_blocks_at_mode(mode))
    allows = not blocks

    if allows:
        if v == "sandbox":
            summary = f"Wonder sandboxed imagination in {mode} mode (ingress allows with scrutiny)."
        else:
            summary = f"Wonder {v} in {mode} mode."
    else:
        summary = (
            "Wonder forbids conceptual exploration"
            + (f" ({', '.join(violation_codes[:3])})" if violation_codes else "")
            + "."
        )

    return {
        "allows": allows,
        "status": "pass" if allows else "fail",
        "summary": summary,
        "wonder_verdict": verdict,
        "reason_codes": violation_codes,
    }
