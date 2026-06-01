"""Operator readout for Jarvis previews."""

from __future__ import annotations

from typing import Any


def build_cloud_forge_readout(
    cloud_forge_bundle: dict[str, Any],
    *,
    ledger_record_id: str | None = None,
    promotion: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compact Jarvis-facing summary of rail decision + plan."""
    decision = dict(cloud_forge_bundle.get("rail_decision") or {})
    plan = dict(cloud_forge_bundle.get("cognition_plan") or {})
    template = dict(plan.get("template") or {})
    rail = str(decision.get("rail") or "UNKNOWN")
    risk = str(decision.get("risk") or "UNKNOWN")

    summary_parts = [
        f"Cloud Forge rail: {rail}",
        f"risk={risk}",
    ]
    if plan.get("domain_template"):
        summary_parts.append(f"domain={plan['domain_template']}")
    if template.get("summary"):
        summary_parts.append(str(template["summary"]))

    cache_resolution = dict(cloud_forge_bundle.get("cache_resolution") or {})
    if cache_resolution.get("status") == "hit":
        summary_parts.append(f"cache_hit={cache_resolution.get('layer')}")

    placement = dict(cloud_forge_bundle.get("cloud_placement") or {})
    if placement.get("slice_id"):
        summary_parts.append(f"slice={placement['slice_id']}")
    if placement.get("priority", {}).get("priority_class"):
        summary_parts.append(f"priority={placement['priority']['priority_class']}")

    return {
        "contract_version": cloud_forge_bundle.get("contract_version"),
        "rail": rail,
        "risk": risk,
        "novelty": decision.get("novelty"),
        "law_ceiling": decision.get("law_ceiling"),
        "rationale_codes": list(decision.get("rationale_codes") or []),
        "steps": list(plan.get("steps") or []),
        "model_tier": plan.get("model_tier"),
        "parallelism": plan.get("parallelism"),
        "cache_mode": plan.get("cache_mode"),
        "speculation": plan.get("speculation"),
        "domain_template": plan.get("domain_template"),
        "template_prefetch_docs": list(template.get("prefetch_docs") or []),
        "summary": "; ".join(summary_parts),
        "claim_status": decision.get("claim_status", "asserted"),
        "ledger_record_id": ledger_record_id,
        "promotion_status": (promotion or {}).get("classification"),
        "cache_resolution": cache_resolution or None,
        "cached_answer": cloud_forge_bundle.get("cached_answer"),
        "cloud_placement": cloud_forge_bundle.get("cloud_placement"),
        "session_prewarm": cloud_forge_bundle.get("session_prewarm"),
        "runtime_effect": "readout_only",
    }
