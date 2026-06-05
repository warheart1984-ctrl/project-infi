"""Governed hot-update of operator reward policy v1.1."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.ugr.rewards.reward_policy import DEFAULT_POLICY, _default_policy_path, invalidate_reward_policy_cache


def governance_apply_enabled() -> bool:
    raw = os.getenv("URG_GOVERNANCE_APPLY", "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _merge_policy(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if key == "economy" and isinstance(value, dict):
            merged["economy"] = {**dict(merged.get("economy") or {}), **value}
        elif key in ("discovery", "promotion", "adoption", "spend", "transfer") and isinstance(value, dict):
            merged[key] = {**dict(merged.get(key) or {}), **value}
        else:
            merged[key] = value
    return merged


def apply_reward_policy_update(
    policy_patch: dict[str, Any],
    *,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Apply reward policy patch when URG_GOVERNANCE_APPLY=1."""
    _ = tenant_id  # reserved for future per-tenant overlays
    if not governance_apply_enabled():
        return {
            "status": "blocked",
            "summary": "reward policy update requires URG_GOVERNANCE_APPLY=1",
        }

    patch = dict(policy_patch or {})
    if not patch:
        return {"status": "rejected", "summary": "empty policy_patch"}

    path = _default_policy_path()
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else dict(DEFAULT_POLICY)
    merged = _merge_policy(current, patch)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged, indent=2, sort_keys=True), encoding="utf-8")
    invalidate_reward_policy_cache()

    return {
        "status": "ok",
        "summary": "reward policy updated",
        "policy_version": merged.get("version"),
        "path": str(path),
    }
