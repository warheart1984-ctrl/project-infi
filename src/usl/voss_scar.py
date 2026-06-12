"""Voss Δ→scar derivation and cycle-boundary bridge."""

from __future__ import annotations

import hashlib
from typing import Any

from src.usl.types import ActorInfo, VossInfo

EMPTY_DEBT_SENTINEL = (
    "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)


def _sha256_hex(*parts: bytes | str) -> str:
    h = hashlib.sha256()
    for part in parts:
        if isinstance(part, str):
            part = part.encode("utf-8")
        h.update(part)
    return f"sha256:{h.hexdigest()}"


def _strip_prefix(value: str) -> str:
    if value.startswith("sha256:"):
        return value[7:]
    return value


def derive_lambda_coupling_id(
    pre_state_hash: str,
    capability_id: str,
    post_state_hash: str,
    actor: ActorInfo,
) -> str:
    """lambda_coupling_id = SHA256(pre || capability_id || post || actor_blob)."""
    return _sha256_hex(
        _strip_prefix(pre_state_hash),
        capability_id,
        _strip_prefix(post_state_hash),
        actor.blob(),
    )


def derive_scar_id(lambda_coupling_id: str, decision: str, cycle_id: int | str) -> str:
    """scar_id = SHA256(lambda_coupling_id || decision || cycle_id)."""
    return _sha256_hex(
        _strip_prefix(lambda_coupling_id),
        decision.lower(),
        str(cycle_id),
    )


def derive_debt_id(pending_obligations: list[dict[str, Any]] | None = None) -> str:
    """Hash pending obligations; empty sentinel when none."""
    if not pending_obligations:
        return EMPTY_DEBT_SENTINEL
    import json

    payload = json.dumps(pending_obligations, sort_keys=True, separators=(",", ":"))
    return _sha256_hex(payload)


def bind_voss(
    *,
    pre_state_hash: str,
    post_state_hash: str,
    capability_id: str,
    actor: ActorInfo,
    decision: str,
    cycle_id: int | str,
    lane_id: str,
    pending_obligations: list[dict[str, Any]] | None = None,
) -> VossInfo:
    """Compute full Voss binding fields for a transition."""
    lambda_id = derive_lambda_coupling_id(
        pre_state_hash, capability_id, post_state_hash, actor
    )
    scar_id = derive_scar_id(lambda_id, decision, cycle_id)
    debt_id = derive_debt_id(pending_obligations)
    return VossInfo(
        lambda_coupling_id=lambda_id,
        debt_id=debt_id,
        scar_id=scar_id,
        cycle_id=cycle_id,
        lane_id=lane_id,
    )


def constitutional_disposition(decision: str) -> str:
    """Map law decision to voss_binding.BindingDisposition name when constitutional."""
    mapping = {
        "allow": "BOUND",
        "degrade": "PARTIAL",
        "deny": "REJECTED",
        "quarantine": "REJECTED",
        "redirect": "PARTIAL",
    }
    return mapping.get(decision.lower(), "PARTIAL")
