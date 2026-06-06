"""Tests for Infinity-1 operator dashboard snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.operator_infinity1_dashboard import (
    build_infinity1_dashboard_snapshot,
    build_seam_health_poll,
)

ROOT = Path(__file__).resolve().parents[1]
SEAM_ARTIFACT = ROOT / "ci-artifacts" / "seam_discovery_report.json"


def test_dashboard_snapshot_has_required_keys():
    snap = build_infinity1_dashboard_snapshot()
    assert snap.get("runtime_effect") == "readout_only"
    assert snap.get("dashboard_id") == "aais.operator.infinity1_dashboard"
    assert "health" in snap
    assert "seam_stress" in snap
    assert "live_stress" in snap
    assert "ledger_digest" in snap
    assert "brain" in snap
    assert "plugins" in snap
    assert "workflow_stack" in snap
    assert "quick_links" in snap
    assert len(snap["quick_links"]) >= 4
    assert "monitoring" in snap
    assert snap["monitoring"].get("runtime_effect") == "readout_only"


def test_monitoring_poll_lightweight():
    from src.operator_infinity1_dashboard import build_monitoring_poll

    poll = build_monitoring_poll()
    assert "alerts" in poll
    assert "alert_count" in poll


def test_seam_stress_loads_artifact_when_present():
    if not SEAM_ARTIFACT.is_file():
        pytest.skip("seam_discovery_report.json not present")
    snap = build_infinity1_dashboard_snapshot()
    seam = snap["seam_stress"]
    report = json.loads(SEAM_ARTIFACT.read_text(encoding="utf-8"))
    assert seam.get("total_probes") == report.get("summary", {}).get("total_probes")
    assert seam.get("audit_doc") == "docs/audit/SEAM_STRESS_RUN_2026-06-06.md"


def test_seam_health_poll_is_lightweight():
    poll = build_seam_health_poll()
    assert poll.get("runtime_effect") == "readout_only"
    assert "health" in poll
    assert "seam_stress" in poll
    assert "ledger_digest" not in poll


def test_workflow_stack_lists_gates():
    snap = build_infinity1_dashboard_snapshot()
    gates = snap["workflow_stack"]["gates"]
    ids = {g["id"] for g in gates}
    assert "library-gate" in ids
    assert "plug-adapter-gate" in ids
