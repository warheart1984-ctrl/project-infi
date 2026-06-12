"""Deterministic 39-field canonical serializer for Voss transitions."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from src.usl.types import VossTransition

_HASH_PREFIX = re.compile(r"^sha256:", re.IGNORECASE)


def _normalize_hash(value: str) -> str:
    if not value:
        return ""
    return _HASH_PREFIX.sub("", value.strip()).lower()


def _normalize_enum(value: str) -> str:
    return str(value).strip().lower()


def _normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        if value.startswith("sha256:") or (
            len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)
        ):
            return _normalize_hash(value)
        return value
    return str(value)


def _field_pairs(transition: VossTransition) -> list[tuple[str, str]]:
    """Fixed 39-field order for canonical serialization."""
    extra = transition.capability.resource.extra or {}
    ds = transition.state.delta_summary
    pairs: list[tuple[str, str]] = [
        ("version", _normalize_scalar(transition.version)),
        ("transition_id", _normalize_scalar(transition.transition_id)),
        ("timestamp", _normalize_scalar(transition.timestamp)),
        ("actor.binary_id", _normalize_hash(transition.actor.binary_id)),
        ("actor.profile_id", _normalize_scalar(transition.actor.profile_id)),
        ("actor.principal_id", _normalize_scalar(transition.actor.principal_id)),
        ("actor.sigil_id", _normalize_scalar(transition.actor.sigil_id)),
        ("context.os_family", _normalize_enum(transition.context.os_family)),
        ("context.process_id", _normalize_scalar(transition.context.process_id)),
        ("context.thread_id", _normalize_scalar(transition.context.thread_id)),
        ("context.session_id", _normalize_scalar(transition.context.session_id)),
        ("context.usl_node_id", _normalize_scalar(transition.context.usl_node_id)),
        ("capability.capability_id", _normalize_scalar(transition.capability.capability_id)),
        ("capability.ceiling_id", _normalize_scalar(transition.capability.ceiling_id)),
        ("capability.resource.kind", _normalize_scalar(transition.capability.resource.kind)),
        ("capability.resource.locator", _normalize_scalar(transition.capability.resource.locator)),
        ("capability.resource.extra.method", _normalize_scalar(extra.get("method", ""))),
        ("capability.resource.extra.mode", _normalize_scalar(extra.get("mode", ""))),
        ("capability.resource.extra.direction", _normalize_scalar(extra.get("direction", ""))),
        ("state.pre_state_hash", _normalize_hash(transition.state.pre_state_hash)),
        ("state.post_state_hash", _normalize_hash(transition.state.post_state_hash)),
        ("state.delta_hash", _normalize_hash(transition.state.delta_hash)),
        ("state.delta_summary.bytes_written", _normalize_scalar(ds.bytes_written)),
        ("state.delta_summary.bytes_read", _normalize_scalar(ds.bytes_read)),
        ("state.delta_summary.objects_created", _normalize_scalar(ds.objects_created)),
        ("state.delta_summary.objects_deleted", _normalize_scalar(ds.objects_deleted)),
        ("state.delta_summary.capabilities_granted", _normalize_scalar(ds.capabilities_granted)),
        ("state.delta_summary.capabilities_revoked", _normalize_scalar(ds.capabilities_revoked)),
        ("law.policy_id", _normalize_scalar(transition.law.policy_id)),
        ("law.lawbook_id", _normalize_scalar(transition.law.lawbook_id)),
        ("law.decision", _normalize_enum(transition.law.decision)),
        ("law.decision_reason", _normalize_scalar(transition.law.decision_reason)),
        ("law.decision_detail", _normalize_scalar(transition.law.decision_detail)),
        ("voss.lambda_coupling_id", _normalize_hash(transition.voss.lambda_coupling_id)),
        ("voss.debt_id", _normalize_hash(transition.voss.debt_id)),
        ("voss.scar_id", _normalize_hash(transition.voss.scar_id)),
        ("voss.cycle_id", _normalize_scalar(transition.voss.cycle_id)),
        ("voss.lane_id", _normalize_scalar(transition.voss.lane_id)),
        ("crypto.prev_ledger_root", _normalize_hash(transition.crypto.prev_ledger_root)),
    ]
    return pairs


def canonical_bytes(transition: VossTransition) -> bytes:
    """Serialize transition to canonical UTF-8 bytes (no whitespace, omit null fields)."""
    parts: list[str] = []
    for key, value in _field_pairs(transition):
        if value == "":
            continue
        if key.startswith("state.delta_summary.") and value == "0":
            continue
        parts.append(f"{key}={value}")
    return "|".join(parts).encode("utf-8")


def event_hash(transition: VossTransition) -> str:
    """SHA256 of canonical bytes."""
    digest = hashlib.sha256(canonical_bytes(transition)).hexdigest()
    return f"sha256:{digest}"


def ledger_root(prev_root: str, evt_hash: str) -> str:
    """ledger_root = SHA256(prev_ledger_root || event_hash) as hex strings."""
    prev = _normalize_hash(prev_root).encode("utf-8")
    evt = _normalize_hash(evt_hash).encode("utf-8")
    digest = hashlib.sha256(prev + evt).hexdigest()
    return f"sha256:{digest}"
