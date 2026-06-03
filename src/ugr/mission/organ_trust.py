"""Organ trust scores — derived from execution_committed mission receipts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ugr.mission.tenant_manifold import tenant_path_slug
from src.ugr.platform.tenant_registry import normalize_tenant_id

TRUST_SHADOW_THRESHOLD = 0.3
TRUST_LIVE_THRESHOLD = 0.7
TRUST_EMA_ALPHA = 0.15


def _trust_store_path(tenant_id: str) -> Path:
    slug = tenant_path_slug(normalize_tenant_id(tenant_id))
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "tenants" / slug / "organ-trust.json"


def load_trust_scores(tenant_id: str) -> dict[str, float]:
    path = _trust_store_path(tenant_id)
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): float(v) for k, v in dict(payload.get("scores") or {}).items()}


def save_trust_scores(tenant_id: str, scores: dict[str, float]) -> None:
    path = _trust_store_path(tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"scores": scores}, indent=2) + "\n",
        encoding="utf-8",
    )


def effective_trust(organ_trust: float, tenant_id: str, organ_id: str) -> float:
    stored = load_trust_scores(tenant_id).get(organ_id)
    if stored is not None:
        return float(stored)
    return float(organ_trust)


def update_trust_from_receipt(
    receipt_schema: dict[str, Any],
    *,
    steps: list[dict[str, Any]],
    tenant_id: str,
) -> dict[str, float]:
    """Bump trust for organs with execution_committed on completed missions."""
    if str(receipt_schema.get("outcome") or "") != "completed":
        return load_trust_scores(tenant_id)
    scores = load_trust_scores(tenant_id)
    for step in steps:
        if not step.get("execution_committed"):
            continue
        organ_id = str(step.get("organ_id") or "").strip()
        if not organ_id:
            continue
        prior = scores.get(organ_id, 0.5)
        scores[organ_id] = min(1.0, prior + TRUST_EMA_ALPHA * (1.0 - prior))
    save_trust_scores(tenant_id, scores)
    return scores


def organ_eligible_for_live(trust: float) -> bool:
    return trust >= TRUST_LIVE_THRESHOLD


def organ_requires_shadow(trust: float) -> bool:
    return trust < TRUST_SHADOW_THRESHOLD


def resolve_execution_mode_for_organ(
    requested_mode: str,
    organ_trust: float,
) -> str:
    """Downgrade LIVE to SHADOW when organ trust is low."""
    from src.ugr.mission.execution_policy import EXECUTION_MODE_LIVE, EXECUTION_MODE_SHADOW

    mode = str(requested_mode or "").upper()
    if mode == EXECUTION_MODE_LIVE and organ_requires_shadow(organ_trust):
        return EXECUTION_MODE_SHADOW
    return mode
