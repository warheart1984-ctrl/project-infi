"""Aggregate UGR + Cloud Forge operator console snapshot."""

# Mythic: Snapshot
# Engineering: SnapshotEngine
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.ugr.cloud.mesh_config import deployment_mode, load_mesh_config
from src.ugr.operator_console.debt_register import debt_summary
from src.ugr.operator_console.forge_platform import load_forge_platform_dashboard
from src.ugr.operator_console.mesh_health import poll_mesh_health
from src.ugr.operator_console.readout import build_operator_readout
from src.ugr.operator_console.trace_viewer import load_deliberation_traces


CONSOLE_VERSION = "1.1"
CONSOLE_ID = "aais.operator.ugr_cloud_console"

GATE_COMMANDS = [
    "make ugr-trust-bundle-gate",
    "make ugr-cloud-gate",
    "make ugr-embryo-gate",
    "make ugr-causal-graph-gate",
    "make forge-platform-gate",
]


def _runtime_root() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


def _load_trust_bundle_status(runtime_root: Path) -> dict[str, Any]:
    proof_path = runtime_root / "trust-bundles" / "latest" / "proof_bundle.json"
    hash_path = runtime_root / "trust-bundles" / "latest" / "proof_bundle.sha256"
    if not proof_path.exists():
        return {
            "status": "missing",
            "overall_status": "missing",
            "claim_status": "asserted",
            "summary": "No local proof bundle — run make ugr-trust-bundle-gate",
            "proof_path": str(proof_path),
        }
    payload = json.loads(proof_path.read_text(encoding="utf-8"))
    stored_hash = hash_path.read_text(encoding="utf-8").strip() if hash_path.exists() else ""
    return {
        "status": "ok",
        "overall_status": payload.get("overall_status"),
        "claim_status": "proven" if payload.get("overall_status") == "pass" else "asserted",
        "bundle_id": payload.get("bundle_id"),
        "generated_at_utc": payload.get("generated_at_utc"),
        "cross_profile_parity": payload.get("cross_profile_parity"),
        "verification_command": payload.get("verification_command"),
        "proof_path": str(proof_path),
        "proof_bundle_sha256": stored_hash,
    }


def _build_ugr_snapshot(*, runtime: Any | None = None) -> dict[str, Any]:
    embryo_health: dict[str, Any] = {"status": "unknown"}
    graph_stats = None
    region_health = None
    try:
        from src.ugr.embryo.health import probe_embryo_health

        embryo_health = probe_embryo_health(runtime=runtime)
    except Exception as exc:
        embryo_health = {"status": "error", "summary": str(exc)}

    if runtime is not None and hasattr(runtime, "ledger"):
        try:
            graph_stats = runtime.ledger.graph_index_stats()
            region_health = runtime.ledger.region_health()
        except Exception:
            graph_stats = None
            region_health = None

    flags = {
        "causal_graph": os.getenv("UGR_CAUSAL_GRAPH_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
        "graph_index": os.getenv("UGR_GRAPH_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
        "graph_query_backend": os.getenv("UGR_GRAPH_QUERY_BACKEND", "jsonl_memory"),
        "llm_execute": os.getenv("UGR_LLM_EXECUTE", "").strip().lower() in {"1", "true", "yes", "on"},
        "platform": os.getenv("UGR_PLATFORM_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
    }

    mesh = load_mesh_config()
    return {
        "status": embryo_health.get("status", "ok"),
        "deployment_mode": deployment_mode(),
        "mesh_cluster_id": mesh.cluster_id,
        "mesh_services": sorted(mesh.services.keys()),
        "embryo": embryo_health,
        "graph_index": graph_stats,
        "region_health": region_health,
        "feature_flags": flags,
        "api_routes": {
            "v0_health": "/api/ugr/v0/health",
            "v1_health": "/api/ugr/v1/health",
            "v1_regions": "/api/ugr/v1/regions/health",
            "deliberate": "/api/ugr/deliberate",
        },
    }


def _build_cloud_forge_snapshot() -> dict[str, Any]:
    rail = os.getenv("CLOUD_FORGE_DEFAULT_RAIL", "NORMAL").strip().upper() or "NORMAL"
    bundle = {
        "contract_version": "1.0",
        "rail_decision": {
            "rail": rail,
            "risk": os.getenv("CLOUD_FORGE_DEFAULT_RISK", "LOW"),
            "rationale": "operator_console_default",
        },
        "observed": os.getenv("UGR_CLOUD_FORGE_OBSERVED", "").strip().lower() in {"1", "true", "yes", "on"},
    }
    try:
        from src.cloud_forge.readout import build_cloud_forge_readout

        readout = build_cloud_forge_readout(bundle)
    except Exception as exc:
        readout = {
            "summary": f"Cloud Forge readout unavailable: {exc}",
            "claim_status": "asserted",
            "runtime_effect": "readout_only",
        }
    return {
        "rail": rail,
        "readout": readout,
        "routes": {
            "forge_platform_gate": "make forge-platform-gate",
            "ugr_deliberate": "/api/ugr/deliberate",
        },
        "claim_status": readout.get("claim_status", "asserted"),
    }


def _build_rewards_snapshot() -> dict[str, Any]:
    try:
        from src.ugr.rewards.reward_issuer import rewards_enabled, rewards_shadow_only
        from src.ugr.rewards.reward_policy import load_reward_policy

        policy = load_reward_policy()
        return {
            "status": "ok",
            "enabled": rewards_enabled(),
            "shadow_only": rewards_shadow_only(),
            "economy": dict(policy.get("economy") or {}),
            "purchase": dict(policy.get("purchase") or {}),
            "routes": {
                "discover": "/api/ugr/discover/contribution",
                "spend": "/api/ugr/rewards/spend",
                "purchase": "/api/ugr/credits/purchase",
                "operator_profile": "/api/ugr/reward/operator/<operator_id>",
            },
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}


def build_operator_console_snapshot(*, runtime: Any | None = None) -> dict[str, Any]:
    """Build advisory operator console snapshot for UI + workbench."""
    if runtime is None:
        try:
            from src.ugr.unified_runtime import build_ugr_runtime

            runtime = build_ugr_runtime()
        except Exception:
            runtime = None

    runtime_root = _runtime_root()
    trust = _load_trust_bundle_status(runtime_root)
    debt = debt_summary()
    ugr = _build_ugr_snapshot(runtime=runtime)
    forge = _build_cloud_forge_snapshot()
    mesh_health = poll_mesh_health()
    traces = load_deliberation_traces(runtime=runtime, limit=10)
    forge_platform = load_forge_platform_dashboard(live_checks=False)

    proven_debt = debt.get("proven_claims", 0)
    trust_proven = trust.get("claim_status") == "proven" and trust.get("overall_status") == "pass"
    overall_claim = "proven" if trust_proven and proven_debt >= 1 else "asserted"

    snapshot = {
        "console_id": CONSOLE_ID,
        "console_version": CONSOLE_VERSION,
        "status": "ok",
        "claim_status": overall_claim,
        "runtime_effect": "readout_only",
        "ugr": ugr,
        "cloud_forge": forge,
        "mesh_health": mesh_health,
        "deliberation_traces": traces,
        "forge_platform": forge_platform,
        "trust_bundle": trust,
        "debt_register": debt,
        "operator_rewards": _build_rewards_snapshot(),
        "gates": GATE_COMMANDS + ["make ugr-rewards-gate"],
        "verification_command": "make ugr-operator-console-gate",
    }
    snapshot["readout"] = build_operator_readout(snapshot)
    from src.aais_ul_substrate import wrap_runtime_snapshot

    return wrap_runtime_snapshot(snapshot)
