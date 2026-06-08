"""Offline + optional live tests for federation chaos hammer."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path


def test_civilizational_get_routes_defined():
    mod = importlib.import_module("tools.stress.federation_chaos_hammer")
    assert len(mod.CIVILIZATIONAL_GET_ROUTES) == 8
    assert all(p.startswith("/api/operator/") for p in mod.CIVILIZATIONAL_GET_ROUTES)


def test_civilizational_subsystems_cover_four_arcs():
    mod = importlib.import_module("tools.stress.federation_chaos_hammer")
    labels = {s["label"] for s in mod.CIVILIZATIONAL_SUBSYSTEMS}
    assert labels == {
        "norm_federation",
        "diplomacy",
        "constitutional_evolution",
        "governed_civilization",
    }


def test_observe_and_adopt_abuse_case_builders():
    mod = importlib.import_module("tools.stress.federation_chaos_hammer")
    observe = mod.build_observe_abuse_cases()
    adopt = mod.build_adopt_abuse_cases()
    assert len(observe) == 5
    assert len(adopt) == 4
    assert adopt[0][0] == "empty_body"


def test_ugr_federation_mission_builder():
    mod = importlib.import_module("tools.stress.federation_chaos_hammer")
    missions = mod.build_ugr_federation_missions()
    assert len(missions) == 5
    missing = next(name for name, payload in missions if name == "missing_grant_id")
    assert missing == "missing_grant_id"
    peer_step = missions[0][1]["steps"][1]
    assert peer_step.get("federation_peer_tenant") == "tenant:contoso"
    assert "federation_grant_id" not in peer_step


def test_federation_graph_grant_ids_non_empty():
    mod = importlib.import_module("tools.stress.federation_chaos_hammer")
    assert len(mod.FEDERATION_GRAPH_GRANT_IDS) >= 5


def test_live_federation_chaos_when_server_up(tmp_path, monkeypatch):
    mod = importlib.import_module("tools.stress.federation_chaos_hammer")
    common = importlib.import_module("tools.stress._chaos_common")

    if not common.server_reachable():
        import pytest

        pytest.skip("AAIS not reachable at AAIS_STRESS_BASE")

    artifact_dir = tmp_path / "ci-artifacts"
    artifact_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(common, "ROOT", tmp_path)

    summary = mod.run_federation_chaos(skip_ugr=False)
    assert summary.get("fatal") is not True
    assert summary.get("server_still_healthy") is True
    assert summary.get("server_errors_5xx", 1) == 0
    assert summary.get("unexpected_failures", 1) == 0
    assert summary.get("total_probes", 0) >= 80

    report_path = artifact_dir / "federation_chaos_report.json"
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert "summary" in payload
    assert payload["summary"]["server_errors_5xx"] == 0
