"""Offline + optional live tests for USL Megaton Chaos Hammer."""

from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_megaton_module_imports():
    mod = importlib.import_module("tools.stress.usl_megaton_chaos_hammer")
    assert hasattr(mod, "run_megaton_chaos")
    assert hasattr(mod, "hammer_phase1_gate")


def _isolate_hammer_fixtures(mod, tmp_path, monkeypatch):
    from tests.fixtures.usl.build_fixtures import ensure_fixtures

    fixture_root = tmp_path / "usl-fixtures"
    paths = mod._snapshot_fixture_paths(*ensure_fixtures(fixture_root))
    monkeypatch.setattr(mod, "_FIXTURE_PATHS", paths)
    monkeypatch.setattr(mod, "_ensure_fixture_paths", lambda: paths)


def test_megaton_phase1_offline_zero_unexpected(tmp_path, monkeypatch):
    mod = importlib.import_module("tools.stress.usl_megaton_chaos_hammer")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "USL_BASE", "http://127.0.0.1:1")
    _isolate_hammer_fixtures(mod, tmp_path, monkeypatch)

    summary = mod.run_megaton_chaos(phase="1", rounds=2)
    assert summary.get("unexpected_failures", 1) == 0
    assert summary.get("total_probes", 0) > 20

    report_path = tmp_path / "ci-artifacts" / "usl_megaton_chaos_report.json"
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["summary"]["unexpected_failures"] == 0


def test_megaton_all_phases_offline(tmp_path, monkeypatch):
    mod = importlib.import_module("tools.stress.usl_megaton_chaos_hammer")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "USL_BASE", "http://127.0.0.1:1")
    _isolate_hammer_fixtures(mod, tmp_path, monkeypatch)

    summary = mod.run_megaton_chaos(phase="all", rounds=1)
    assert summary.get("unexpected_failures", 1) == 0
    assert summary.get("total_probes", 0) >= 40


def test_megaton_live_usl_health_when_up(monkeypatch):
    mod = importlib.import_module("tools.stress.usl_megaton_chaos_hammer")
    status, _ = mod._usl_health()
    if status != 200:
        import pytest

        pytest.skip("USL not reachable at USL_STRESS_BASE")

    summary = mod.run_megaton_chaos(phase="1", rounds=1)
    assert summary.get("unexpected_failures", 1) == 0


def test_megaton_require_live_fails_when_unreachable(tmp_path, monkeypatch):
    mod = importlib.import_module("tools.stress.usl_megaton_chaos_hammer")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "USL_BASE", "http://127.0.0.1:1")
    _isolate_hammer_fixtures(mod, tmp_path, monkeypatch)

    summary = mod.run_megaton_chaos(phase="1", rounds=2, require_live=True)
    assert summary.get("pass") is False
    assert summary.get("health_skips", -1) == 0
    assert summary.get("require_live") is True

    report_path = tmp_path / "ci-artifacts" / "usl_megaton_chaos_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    names = [r["name"] for r in payload.get("sample_results", [])]
    assert any(n.startswith("p1_health_required") for n in names)
    assert not any(n.startswith("p1_health_skip") for n in names)
