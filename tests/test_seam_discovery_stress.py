"""Offline smoke tests for seam discovery route harvest."""

from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_harvest_flask_routes_includes_operator_and_jarvis_status():
    mod = importlib.import_module("tools.stress.seam_discovery_stress")
    routes = mod.harvest_flask_routes()
    rules = {r.rule for r in routes}
    assert "/api/operator/ledger" in rules
    assert any(r.endswith("/status") and "/api/jarvis/" in r for r in rules)


def test_harvest_genome_api_surfaces_returns_entries():
    mod = importlib.import_module("tools.stress.seam_discovery_stress")
    surfaces = mod.harvest_genome_api_surfaces()
    assert surfaces
    assert any(s["path"].endswith("/status") for s in surfaces)


def test_offline_discovery_writes_report(tmp_path, monkeypatch):
    mod = importlib.import_module("tools.stress.seam_discovery_stress")
    artifact_dir = tmp_path / "ci-artifacts"
    monkeypatch.setattr(mod, "ARTIFACT_DIR", artifact_dir)

    report = mod.run_discovery(offline=True, log_seams=False, write_records=False)
    out = artifact_dir / "seam_discovery_report.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["offline"] is True
    assert payload["route_inventory"]["total_routes"] > 0
    assert report.summary["mode"] == "offline_harvest"


def test_live_api_stress_auto_discover_paths():
    mod = importlib.import_module("tools.stress.live_api_stress")
    paths = mod.discover_jarvis_status_paths()
    assert paths
    assert all(p.startswith("/api/jarvis/") and p.endswith("/status") for p in paths)
