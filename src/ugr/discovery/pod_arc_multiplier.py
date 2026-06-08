"""Governance arc tier detection and Discovery Pod reward multipliers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

UGR_POD_ARC_MULTIPLIER_ENV = "UGR_POD_ARC_MULTIPLIER"
UGR_POD_ARC_MULTIPLIER_LOW_ENV = "UGR_POD_ARC_MULTIPLIER_LOW"
UGR_POD_ARC_MULTIPLIER_MED_ENV = "UGR_POD_ARC_MULTIPLIER_MED"
UGR_POD_ARC_MULTIPLIER_MED_HIGH_ENV = "UGR_POD_ARC_MULTIPLIER_MED_HIGH"
UGR_POD_ARC_MULTIPLIER_HIGH_ENV = "UGR_POD_ARC_MULTIPLIER_HIGH"
UGR_POD_ARC_MULTIPLIER_CIVILIZATIONAL_ENV = "UGR_POD_ARC_MULTIPLIER_CIVILIZATIONAL"

TIER_NONE = "none"
TIER_LOW = "low"
TIER_MED = "med"
TIER_MED_HIGH = "med_high"
TIER_BEYOND_BODY = "beyond_body"
TIER_CIVILIZATIONAL = "civilizational"

_TIER_RANK = {
    TIER_NONE: 0,
    TIER_LOW: 1,
    TIER_MED: 2,
    TIER_MED_HIGH: 3,
    TIER_BEYOND_BODY: 4,
    TIER_CIVILIZATIONAL: 5,
}


@dataclass
class PodArcContext:
    tier: str = TIER_NONE
    multiplier: float = 1.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "governance_arc_tier": self.tier,
            "pod_reward_multiplier": self.multiplier,
            "arc_signals": list(self.signals),
        }


def _env_multiplier(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def arc_multipliers_from_policy(policy: dict[str, Any] | None = None) -> dict[str, float]:
    """Resolve per-tier multipliers from reward/admission policy + env overrides."""
    pol = dict(policy or {})
    section = dict(pol.get("pod_arc_multipliers") or {})
    default = _env_multiplier(UGR_POD_ARC_MULTIPLIER_ENV, float(section.get("default") or 1.0))
    low_default = float(section.get("low") or 2.0)
    med_default = float(section.get("med") or section.get("medium") or 4.0)
    med_high_default = float(
        section.get("med_high") or section.get("med-high") or section.get("medhigh") or 7.0
    )
    high_default = float(section.get("high") or section.get("beyond_body") or 10.0)
    civ_default = float(section.get("civilizational") or 10.0)
    return {
        TIER_NONE: default if default > 0 else 1.0,
        TIER_LOW: _env_multiplier(UGR_POD_ARC_MULTIPLIER_LOW_ENV, low_default),
        TIER_MED: _env_multiplier(UGR_POD_ARC_MULTIPLIER_MED_ENV, med_default),
        TIER_MED_HIGH: _env_multiplier(UGR_POD_ARC_MULTIPLIER_MED_HIGH_ENV, med_high_default),
        TIER_BEYOND_BODY: _env_multiplier(UGR_POD_ARC_MULTIPLIER_HIGH_ENV, high_default),
        TIER_CIVILIZATIONAL: _env_multiplier(
            UGR_POD_ARC_MULTIPLIER_CIVILIZATIONAL_ENV,
            civ_default,
        ),
    }


def normalize_arc_tier(tier: str, *, default: str = TIER_NONE) -> str:
    """Map user/policy tier labels to canonical arc tier keys."""
    normalized = str(tier or "").strip().lower().replace("-", "_")
    if normalized in {"high", "beyond_body", "beyond_body_arc", "beyond the body"}:
        return TIER_BEYOND_BODY
    if normalized in {"civilizational", "civilizational_arc"}:
        return TIER_CIVILIZATIONAL
    if normalized in {"med_high", "medhigh", "medium_high", "mediumhigh"}:
        return TIER_MED_HIGH
    if normalized in {"med", "medium", "mid"}:
        return TIER_MED
    if normalized in {"low", "baseline_arc"}:
        return TIER_LOW
    if normalized in _TIER_RANK:
        return normalized
    return default


def _tier_from_governance_arc_label(raw: str, tier: str) -> tuple[str, bool]:
    """Map explicit governance_arc / arc_tier string to canonical tier if higher rank."""
    normalized = str(raw or "").strip().lower().replace("-", "_")
    if not normalized:
        return tier, False
    candidate = tier
    changed = False
    if normalized in {"civilizational", "civilizational_arc"}:
        candidate = TIER_CIVILIZATIONAL
        changed = True
    elif normalized in {"high", "beyond_body", "beyond_body_arc"}:
        if _TIER_RANK[TIER_BEYOND_BODY] > _TIER_RANK[candidate]:
            candidate = TIER_BEYOND_BODY
            changed = True
    elif normalized in {"med_high", "medhigh", "medium_high", "mediumhigh"}:
        if _TIER_RANK[TIER_MED_HIGH] > _TIER_RANK[candidate]:
            candidate = TIER_MED_HIGH
            changed = True
    elif normalized in {"med", "medium", "mid"}:
        if _TIER_RANK[TIER_MED] > _TIER_RANK[candidate]:
            candidate = TIER_MED
            changed = True
    elif normalized in {"low", "baseline_arc"}:
        if _TIER_RANK[TIER_LOW] > _TIER_RANK[candidate]:
            candidate = TIER_LOW
            changed = True
    return candidate, changed


def _merge_sources(
    spec_payload: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(spec_payload or {})
    receipt_obj = dict(receipt or {})
    merged: dict[str, Any] = {}
    merged.update(dict(receipt_obj.get("genome_metadata") or {}))
    merged.update(dict(receipt_obj.get("payload") or {}))
    merged.update(payload)
    if receipt_obj.get("contribution_type"):
        merged.setdefault("contribution_type", receipt_obj.get("contribution_type"))
    return merged


def _scan_text_blobs(obj: Any, out: list[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                out.append(f"{key}:{value.lower()}")
            _scan_text_blobs(value, out)
    elif isinstance(obj, list):
        for item in obj:
            _scan_text_blobs(item, out)
    elif isinstance(obj, str):
        out.append(obj.lower())


def _tier_from_numeric(meta: dict[str, Any]) -> tuple[str, list[str]]:
    signals: list[str] = []
    tier = TIER_NONE

    civ_tier = meta.get("civilizational_tier")
    if isinstance(civ_tier, (int, float)):
        civ_int = int(civ_tier)
        if civ_int >= 15:
            signals.append(f"civilizational_tier:{civ_int}")
            tier = TIER_CIVILIZATIONAL
        elif civ_int >= 11:
            signals.append(f"civilizational_tier:{civ_int}")
            if _TIER_RANK[TIER_BEYOND_BODY] > _TIER_RANK[tier]:
                tier = TIER_BEYOND_BODY
        elif civ_int >= 10:
            signals.append(f"civilizational_tier:{civ_int}")
            if _TIER_RANK[TIER_MED_HIGH] > _TIER_RANK[tier]:
                tier = TIER_MED_HIGH
        elif civ_int >= 8:
            signals.append(f"civilizational_tier:{civ_int}")
            if _TIER_RANK[TIER_MED] > _TIER_RANK[tier]:
                tier = TIER_MED
        elif civ_int >= 5:
            signals.append(f"civilizational_tier:{civ_int}")
            if _TIER_RANK[TIER_LOW] > _TIER_RANK[tier]:
                tier = TIER_LOW

    layer = meta.get("anatomical_layer")
    if isinstance(layer, (int, float)):
        layer_int = int(layer)
        if layer_int >= 17:
            signals.append(f"anatomical_layer:{layer_int}")
            tier = TIER_CIVILIZATIONAL
        elif layer_int >= 14:
            signals.append(f"anatomical_layer:{layer_int}")
            if _TIER_RANK[TIER_BEYOND_BODY] > _TIER_RANK[tier]:
                tier = TIER_BEYOND_BODY
        elif layer_int >= 13:
            signals.append(f"anatomical_layer:{layer_int}")
            if _TIER_RANK[TIER_MED_HIGH] > _TIER_RANK[tier]:
                tier = TIER_MED_HIGH
        elif layer_int >= 11:
            signals.append(f"anatomical_layer:{layer_int}")
            if _TIER_RANK[TIER_MED] > _TIER_RANK[tier]:
                tier = TIER_MED
        elif layer_int >= 8:
            signals.append(f"anatomical_layer:{layer_int}")
            if _TIER_RANK[TIER_LOW] > _TIER_RANK[tier]:
                tier = TIER_LOW

    activation = meta.get("activation")
    if isinstance(activation, dict):
        batch_id = str(activation.get("batch_id") or "").lower()
        if batch_id:
            signals.append(f"activation.batch_id:{batch_id}")
            if "civilizational-arc" in batch_id or batch_id.startswith("civilizational"):
                tier = TIER_CIVILIZATIONAL
            elif "beyond-body" in batch_id or batch_id.startswith("beyond-body"):
                if _TIER_RANK[TIER_BEYOND_BODY] > _TIER_RANK[tier]:
                    tier = TIER_BEYOND_BODY

    return tier, signals


def resolve_pod_arc_context(
    *,
    spec_payload: dict[str, Any] | None = None,
    receipt: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> PodArcContext:
    """Classify governance arc tier and pod reward multiplier from spec/receipt metadata."""
    merged = _merge_sources(spec_payload, receipt)
    signals: list[str] = []
    tier = TIER_NONE

    for key in ("governance_arc", "arc_tier", "governance_arc_tier", "body_tier"):
        raw = str(merged.get(key) or "").strip().lower()
        if not raw:
            continue
        signals.append(f"{key}:{raw}")
        mapped, _ = _tier_from_governance_arc_label(raw, tier)
        if _TIER_RANK[mapped] > _TIER_RANK[tier]:
            tier = mapped

    numeric_tier, numeric_signals = _tier_from_numeric(merged)
    signals.extend(numeric_signals)
    if _TIER_RANK[numeric_tier] > _TIER_RANK[tier]:
        tier = numeric_tier

    blobs: list[str] = []
    _scan_text_blobs(merged, blobs)
    for blob in blobs:
        if "civilizational-arc" in blob or "civilizational_arc" in blob:
            signals.append("text:civilizational-arc")
            tier = TIER_CIVILIZATIONAL
        elif "beyond-body" in blob or "beyond_body" in blob:
            signals.append("text:beyond-body")
            if _TIER_RANK[TIER_BEYOND_BODY] > _TIER_RANK[tier]:
                tier = TIER_BEYOND_BODY
        elif "med-high" in blob or "med_high" in blob or "medium-high" in blob:
            signals.append("text:med-high")
            if _TIER_RANK[TIER_MED_HIGH] > _TIER_RANK[tier]:
                tier = TIER_MED_HIGH
        elif blob.endswith(":med") or blob == "med" or " arc:med" in blob or blob.endswith(":medium"):
            signals.append("text:med-arc")
            if _TIER_RANK[TIER_MED] > _TIER_RANK[tier]:
                tier = TIER_MED
        elif blob.endswith(":low") or blob == "low" or " arc:low" in blob:
            signals.append("text:low-arc")
            if _TIER_RANK[TIER_LOW] > _TIER_RANK[tier]:
                tier = TIER_LOW
        elif blob.endswith(":high") or blob == "high" or " arc:high" in blob:
            signals.append("text:high-arc")
            if _TIER_RANK[TIER_BEYOND_BODY] > _TIER_RANK[tier]:
                tier = TIER_BEYOND_BODY

    multipliers = arc_multipliers_from_policy(policy)
    multiplier = float(multipliers.get(tier) or multipliers.get(TIER_NONE) or 1.0)
    if tier == TIER_NONE:
        multiplier = 1.0

    deduped_signals = list(dict.fromkeys(signals))
    return PodArcContext(tier=tier, multiplier=multiplier, signals=deduped_signals)


def tier_rank(tier: str) -> int:
    return int(_TIER_RANK.get(tier, 0))


def apply_pod_arc_multiplier_to_deltas(
    deltas: dict[str, float],
    *,
    multiplier: float,
    arc_context: PodArcContext | None = None,
) -> dict[str, float]:
    """Scale reputation and rail credits when pod arc multiplier > 1."""
    if multiplier <= 1.0:
        return dict(deltas)
    scaled = dict(deltas)
    for key in ("reputation", "rail_credits", "earned_rail_credits"):
        if key in scaled:
            scaled[key] = float(scaled[key]) * multiplier
    scaled["pod_reward_multiplier"] = multiplier
    if arc_context is not None:
        scaled["governance_arc_tier"] = arc_context.tier
    return scaled
