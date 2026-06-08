"""Workflow-family readiness rollups for operator organs layer."""

# Mythic: Workflow Family Readiness
# Engineering: WorkflowFamilyReadinessEngine
from __future__ import annotations

from typing import Any

from src.plug_adapter_runtime import plug_adapter_runtime
from src.plug_discovery import match_plug_pattern
from src.workflow_family_registry import family_by_id, list_workflow_families
from src.workflow_plugin_catalog import workflow_by_id


def _resolve_plug_for_pattern(pattern: str) -> dict[str, Any]:
    pattern = str(pattern or "").strip()
    if not pattern:
        return {"status": "missing", "plug_id": None}
    snapshot = plug_adapter_runtime.registry_snapshot()
    plugs = list(snapshot.get("plugs") or [])
    for plug in plugs:
        plug_id = str(plug.get("plug_id") or "")
        if match_plug_pattern(plug_id, pattern):
            enabled = bool(plug.get("enabled", True))
            return {
                "status": "ready" if enabled else "disabled",
                "plug_id": plug_id,
            }
    if pattern.endswith(".*"):
        prefix = pattern[:-2]
        return {"status": "partial", "plug_id": prefix, "note": "wildcard unresolved"}
    return {"status": "not_found", "plug_id": pattern.rstrip(".*")}


def _bundle_readiness(bundle_id: str) -> dict[str, Any]:
    bundle = workflow_by_id(bundle_id)
    if not bundle:
        return {"bundle_id": bundle_id, "readiness": "missing", "ready_steps": 0, "total_steps": 0}
    steps = list(bundle.get("steps") or [])
    ready = 0
    step_details: list[dict[str, Any]] = []
    for step in steps:
        pattern = str(step.get("plug_pattern") or "")
        resolution = _resolve_plug_for_pattern(pattern)
        if resolution.get("status") == "ready":
            ready += 1
        step_details.append({"plug_pattern": pattern, **resolution})
    total = len(steps)
    if total == 0:
        readiness = "empty"
    elif ready == total:
        readiness = "ready"
    elif ready > 0:
        readiness = "partial"
    else:
        readiness = "missing"
    return {
        "bundle_id": bundle_id,
        "readiness": readiness,
        "ready_steps": ready,
        "total_steps": total,
        "steps": step_details,
    }


def compute_family_readiness(family: dict[str, Any]) -> dict[str, Any]:
    chains = list(family.get("chains") or [])
    chain_rows = []
    ready_chains = 0
    for chain in chains:
        bundle_id = str(chain.get("workflow_bundle_id") or chain.get("chain_id") or "")
        bundle_ready = _bundle_readiness(bundle_id)
        chain_row = {**chain, "bundle_readiness": bundle_ready}
        chain_rows.append(chain_row)
        if bundle_ready.get("readiness") == "ready":
            ready_chains += 1
    total_chains = len(chains)
    if total_chains == 0:
        rollup = "empty"
    elif ready_chains == total_chains:
        rollup = "ready"
    elif ready_chains > 0:
        rollup = "partial"
    else:
        rollup = "prototype"
    routing = dict(family.get("routing") or {})
    declared_status = str(routing.get("status") or "prototype")
    effective_routing = declared_status
    if declared_status != "live" and rollup in {"ready", "partial"}:
        effective_routing = "live"
    return {
        **family,
        "readiness": rollup,
        "ready_chains": ready_chains,
        "total_chains": total_chains,
        "routing_status": effective_routing,
        "routing_status_declared": declared_status,
        "chains": chain_rows,
    }


def list_families_with_readiness(*, repo_root=None) -> list[dict[str, Any]]:
    return [compute_family_readiness(f) for f in list_workflow_families(repo_root=repo_root)]


def family_detail_with_readiness(family_id: str, *, repo_root=None) -> dict[str, Any] | None:
    family = family_by_id(family_id, repo_root=repo_root)
    if not family:
        return None
    detail = compute_family_readiness(family)
    libraries = plug_adapter_runtime.list_libraries()
    mount = dict(family.get("mount") or {})
    prefixes = list(mount.get("plug_pattern_prefixes") or [])
    matched_libraries = [
        lib
        for lib in libraries
        if any(str(lib.get("library_id") or "").startswith(prefix.replace(".", "")) for prefix in prefixes)
        or any(str(lib.get("plug_id") or "").startswith(prefix.rstrip(".")) for prefix in prefixes)
    ]
    detail["libraries"] = matched_libraries[:50]
    detail["library_count"] = len(matched_libraries)
    return detail


def resolve_plug_id_for_step(pattern: str) -> str | None:
    resolution = _resolve_plug_for_pattern(pattern)
    if resolution.get("status") == "ready":
        return str(resolution.get("plug_id") or "") or None
    plug_id = str(resolution.get("plug_id") or "").strip()
    return plug_id or None


def suggest_workflow_family_for_text(text: str) -> str | None:
    try:
        from src.brain_chain_scorer import score_families

        rankings = score_families(text)
        if rankings and float(rankings[0].get("fitness_score") or 0) > 0:
            return str(rankings[0].get("family_id") or "") or None
    except Exception:
        pass
    lowered = str(text or "").lower()
    for family in list_workflow_families():
        signals = list((family.get("routing") or {}).get("intent_signals") or [])
        family_id = str(family.get("identity", {}).get("family_id") or "")
        if any(sig in lowered for sig in signals if sig):
            return family_id
    return None
