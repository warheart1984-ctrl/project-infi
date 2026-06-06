"""Infinity-1 operator dashboard snapshot — seam health, workflow stack, accountability."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "ci-artifacts"
AUDIT_DOC = "docs/audit/SEAM_STRESS_RUN_2026-06-06.md"

WORKFLOW_STACK_GATES = [
    {"id": "library-gate", "label": "Library registry"},
    {"id": "workflow-family-gate", "label": "Workflow families"},
    {"id": "brain-proposal-gate", "label": "Brain contracts"},
    {"id": "plug-adapter-gate", "label": "Plug adapter"},
    {"id": "brain-layer-gate", "label": "Brain layer"},
    {"id": "operator-decision-ledger-gate", "label": "Decision ledger"},
    {"id": "operator-decision-ledger-v2-graph-gate", "label": "Ledger graph v2"},
]

QUICK_LINKS = [
    {"path": "/operator/plugins", "label": "Plugins"},
    {"path": "/operator/brain", "label": "Brain Sessions"},
    {"path": "/operator/ledger", "label": "Decision Ledger"},
    {"path": "/operator/replay/operator_session/global", "label": "Temporal Replay"},
    {"path": "/workflows/approvals", "label": "OTEM Approvals"},
]


def _load_json_artifact(name: str) -> dict[str, Any] | None:
    path = ARTIFACT_DIR / name
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _probe_health() -> dict[str, Any]:
    base = os.environ.get("AAIS_STRESS_BASE", "http://127.0.0.1:8000")
    try:
        import requests

        resp = requests.get(f"{base}/health", timeout=int(os.environ.get("AAIS_SEAM_TIMEOUT", "5")))
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        legacy_error = body.get("legacy_api_mount_error")
        return {
            "reachable": True,
            "status_code": resp.status_code,
            "healthy": body.get("status") == "healthy" and resp.status_code == 200,
            "legacy_api_loaded": body.get("legacy_api_loaded"),
            "legacy_api_mount_error": legacy_error,
            "degraded": body.get("status") != "healthy" or bool(legacy_error),
            "source": "live_probe",
        }
    except Exception:
        seam = _load_json_artifact("seam_discovery_report.json")
        if seam and isinstance(seam.get("health"), dict):
            cached = dict(seam["health"])
            cached["source"] = "seam_discovery_artifact"
            return cached
        return {"reachable": False, "healthy": False, "degraded": True, "source": "unavailable"}


def _seam_stress_summary() -> dict[str, Any]:
    report = _load_json_artifact("seam_discovery_report.json") or {}
    summary = dict(report.get("summary") or {})
    inventory = dict(report.get("route_inventory") or {})
    failures = report.get("failures") or []
    critical_high = int(summary.get("critical_high_count") or 0)
    failure_count = int(summary.get("failure_count") or 0)
    return {
        "generated_at": report.get("generated_at"),
        "base": report.get("base"),
        "total_probes": summary.get("total_probes", 0),
        "failure_count": failure_count,
        "critical_high_count": critical_high,
        "ok_count": summary.get("ok_count", 0),
        "closure_status": "closed" if failure_count == 0 and critical_high == 0 else "open",
        "audit_doc": AUDIT_DOC,
        "route_inventory": inventory,
        "genome_gaps": len((report.get("gaps") or {}).get("genome_declared_missing_from_flask") or []),
    }


def _live_stress_summary() -> dict[str, Any]:
    report = _load_json_artifact("live_stress_report.json") or {}
    return {
        "total_requests": report.get("total_requests", 0),
        "ok": report.get("ok", 0),
        "err": report.get("err", 0),
        "avg_latency_ms": report.get("avg_latency_ms"),
        "p95_latency_ms": report.get("p95_latency_ms"),
        "status_endpoint_count": report.get("status_endpoint_count"),
        "operator_endpoint_count": report.get("operator_endpoint_count"),
        "auto_discover": report.get("auto_discover"),
    }


def _ledger_digest() -> dict[str, Any]:
    try:
        from src.operator_decision_ledger import operator_decision_ledger_store

        digest = operator_decision_ledger_store.build_digest_summary("global")
        return {"status": "ok", "digest": digest}
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}


def _brain_summary() -> dict[str, Any]:
    try:
        from src.brain_session_store import brain_session_store

        sessions = brain_session_store.list_sessions()
        pending = sum(1 for s in sessions if str(s.get("operator_decision") or "") == "pending")
        open_count = sum(1 for s in sessions if str(s.get("status") or "") == "open")
        latest = sessions[-1] if sessions else None
        return {
            "status": "ok",
            "session_count": len(sessions),
            "pending_decisions": pending,
            "open_sessions": open_count,
            "latest_session_id": (latest or {}).get("session_id"),
            "latest_decision": (latest or {}).get("operator_decision"),
            "claim_label": "proposal_only",
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}


def _monitoring_summary() -> dict[str, Any]:
    alerts: list[dict[str, str]] = []
    sentinel_block: dict[str, Any] = {"status": "unknown"}
    rail_block: dict[str, Any] = {"status": "unknown", "force_safe_count": 0, "express_count": 0}
    mesh_block: dict[str, Any] = {"status": "unknown"}

    try:
        from src.operator_health_sentinel_organ import build_operator_health_sentinel_organ_status

        sentinel = build_operator_health_sentinel_organ_status()
        sentinel_block = {"status": "ok", "sentinel": sentinel}
        if sentinel.get("verification_status") not in {"verified", "unknown"}:
            alerts.append({"id": "sentinel-verify", "severity": "medium", "summary": "sentinel verification not verified"})
    except Exception as exc:
        sentinel_block = {"status": "error", "summary": str(exc)}

    try:
        from src.cloud_forge.ledger import RailDecisionLedger

        rows = RailDecisionLedger().read_records(limit=50)
        force_safe = 0
        express = 0
        for row in rows:
            rail = str((row.get("rail_decision") or {}).get("rail") or "").upper()
            if rail == "EXPRESS":
                express += 1
            if "force_safe" in json.dumps(row).lower() or rail == "SAFE":
                force_safe += 1
        rail_block = {
            "status": "ok",
            "record_count": len(rows),
            "force_safe_count": force_safe,
            "express_count": express,
        }
        if express > 10:
            alerts.append({"id": "rail-express-high", "severity": "medium", "summary": f"EXPRESS rail decisions={express}"})
    except Exception as exc:
        rail_block = {"status": "error", "summary": str(exc)}

    try:
        from src.ugr.operator_console.mesh_health import poll_mesh_health

        mesh = poll_mesh_health(timeout=2.0)
        mesh_block = {"status": "ok", "mesh": mesh}
        unhealthy = int(mesh.get("total_count") or 0) - int(mesh.get("healthy_count") or 0)
        if unhealthy > 0:
            alerts.append({"id": "mesh-degraded", "severity": "high", "summary": f"mesh unhealthy services={unhealthy}"})
    except Exception as exc:
        mesh_block = {"status": "error", "summary": str(exc)}

    return {
        "runtime_effect": "readout_only",
        "operator_health_sentinel": sentinel_block,
        "cloud_forge_rail": rail_block,
        "mesh_poll": mesh_block,
        "alert_count": len(alerts),
        "alerts": alerts,
        "claim_label": "proven",
    }


def _plugins_summary() -> dict[str, Any]:
    try:
        from src.plug_adapter_runtime import plug_adapter_runtime

        snapshot = plug_adapter_runtime.registry_snapshot()
        libraries = plug_adapter_runtime.list_libraries()
        workflows = plug_adapter_runtime.list_workflows()
        return {
            "status": "ok",
            "plug_count": snapshot.get("plug_count", 0),
            "enabled_count": snapshot.get("enabled_count", 0),
            "library_count": len(libraries),
            "workflow_count": len(workflows),
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}


def build_infinity1_dashboard_snapshot() -> dict[str, Any]:
    """Read-only Infinity-1 operator dashboard aggregate for console v1.2."""
    seam = _seam_stress_summary()
    health = _probe_health()
    seam_closed = seam.get("closure_status") == "closed"
    health_ok = bool(health.get("healthy")) and not health.get("degraded")
    claim = "proven" if seam_closed and health_ok else "asserted"

    return {
        "dashboard_id": "aais.operator.infinity1_dashboard",
        "dashboard_version": "1.1",
        "runtime_effect": "readout_only",
        "claim_status": claim,
        "health": health,
        "seam_stress": seam,
        "live_stress": _live_stress_summary(),
        "ledger_digest": _ledger_digest(),
        "brain": _brain_summary(),
        "plugins": _plugins_summary(),
        "monitoring": _monitoring_summary(),
        "workflow_stack": {
            "stack_id": "operator-workflow-stack-gate",
            "gates": WORKFLOW_STACK_GATES,
            "verification_command": "make operator-workflow-stack-gate",
            "claim_label": "proven" if seam_closed else "asserted",
        },
        "quick_links": QUICK_LINKS,
        "verification_command": "python tools/stress/seam_discovery_stress.py",
    }


def build_seam_health_poll() -> dict[str, Any]:
    """Lightweight poll payload for dashboard refresh."""
    return {
        "runtime_effect": "readout_only",
        "health": _probe_health(),
        "seam_stress": _seam_stress_summary(),
    }


def build_monitoring_poll() -> dict[str, Any]:
    """Alerts-only poll for dashboard refresh."""
    return _monitoring_summary()
