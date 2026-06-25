"""Extract chainable ids from continuity evidence envelopes."""

from __future__ import annotations

import json
from typing import Any


def parse_payload(raw: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def envelope_law_eval_id(payload: dict[str, Any]) -> str:
    inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    return str(
        payload.get("law_eval_id")
        or payload.get("linked_law_eval_id")
        or inner.get("id")
        or inner.get("law_eval_id")
        or ""
    )


def envelope_mission_id(payload: dict[str, Any]) -> str:
    inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    return str(
        payload.get("mission_id")
        or inner.get("mission_id")
        or (inner.get("context") or {}).get("mission_id")
        or ""
    )


def envelope_asset_id(payload: dict[str, Any]) -> str:
    inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    return str(
        payload.get("asset_id")
        or payload.get("target_asset_id")
        or inner.get("asset_id")
        or ""
    )


def envelope_execution_id(payload: dict[str, Any]) -> str:
    inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    return str(
        payload.get("execution_id")
        or payload.get("event_id")
        or inner.get("execution_id")
        or inner.get("trace_id")
        or inner.get("event_id")
        or ""
    )


def envelope_steward(payload: dict[str, Any]) -> str | None:
    inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    steward = payload.get("steward_identity") or inner.get("steward_id") or inner.get("steward")
    if steward:
        return str(steward)
    identity = inner.get("identity")
    if isinstance(identity, dict) and identity.get("steward_id"):
        return str(identity["steward_id"])
    return None


def envelope_validation_ref(payload: dict[str, Any]) -> str:
    inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    return str(
        payload.get("validation_id")
        or payload.get("validation_evidence_id")
        or inner.get("request_evidence_id")
        or inner.get("validation_id")
        or ""
    )
