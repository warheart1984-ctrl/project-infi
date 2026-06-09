"""Extract conceptual imagination text from bridge packets."""

from __future__ import annotations

from typing import Any

IMAGINATION_FIELD_KEYS = (
    "intent",
    "prompt",
    "claim",
    "reasoning",
    "hypothesis",
    "operator_text",
    "strategy_label",
    "contract",
    "objective",
    "summary",
    "rationale",
    "task",
    "restated_task",
)


def _collect_string(value: Any, *, field: str, spans: list[dict[str, str]], sources: list[str]) -> None:
    text = str(value or "").strip()
    if text:
        spans.append({"text": text, "field": field})
        if field not in sources:
            sources.append(field)


def _walk_nested(payload: dict[str, Any], prefix: str, spans: list[dict[str, str]], sources: list[str]) -> None:
    for key in IMAGINATION_FIELD_KEYS:
        if key in payload:
            _collect_string(payload.get(key), field=f"{prefix}.{key}" if prefix else key, spans=spans, sources=sources)
    contract = payload.get("contract")
    if isinstance(contract, dict):
        for ck, cv in contract.items():
            if isinstance(cv, str):
                _collect_string(cv, field=f"{prefix}.contract.{ck}" if prefix else f"contract.{ck}", spans=spans, sources=sources)
    elif isinstance(contract, str):
        _collect_string(contract, field=f"{prefix}.contract" if prefix else "contract", spans=spans, sources=sources)


def extract_conceptual_text_from_bridge_packet(
    normalized_packet: dict[str, Any],
) -> dict[str, Any]:
    """Harvest imagination-bearing text spans from a normalized bridge packet."""
    packet_type = str(normalized_packet.get("type") or "").strip()
    payload = dict(normalized_packet.get("payload") or {})
    spans: list[dict[str, str]] = []
    sources: list[str] = []

    _walk_nested(payload, "", spans, sources)

    for nested_key in ("exchange", "envelope", "request", "deliberation"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            _walk_nested(nested, nested_key, spans, sources)

    return {
        "packet_id": payload.get("packet_id") or normalized_packet.get("id"),
        "packet_type": packet_type,
        "spans": spans,
        "source_fields": sources,
    }
