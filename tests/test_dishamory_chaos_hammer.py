"""Offline + optional live tests for disharmony chaos hammer."""

from __future__ import annotations

import importlib
import json
from pathlib import Path


def _mod():
    return importlib.import_module("tools.stress.dishamory_chaos_hammer")


def test_phase_a_probe_count():
    mod = _mod()
    assert len(mod.PHASE_A_PROBES) == 8


def test_phase_b_subsystem_probe_counts():
    mod = _mod()
    rnd = 42
    assert len(mod._governance_probes_for_round(rnd)) == 18
    assert len(mod._memory_probes_for_round(rnd)) == 18
    assert len(mod._runtime_probes_for_round(rnd)) == 18
    assert len(mod._federation_probes_for_round(rnd)) == 18


def test_phase_b2_burst_task_count():
    mod = _mod()
    assert len(mod._burst_tasks_for_round(0)) == 32


def test_probes_per_full_round():
    mod = _mod()
    per_round = 8 + 72 + 32 + 10
    assert per_round == 122


def test_disharmony_metrics_defaults():
    mod = _mod()
    d = mod.DisharmonyMetrics().to_dict()
    assert d["governance_drift"] == 0
    assert d["memory_ledger_divergence"] == 0
    assert d["gossip_drift"] == 0
    assert d["split_brain_events"] == 0
    assert d["invariant_violations"] == 0


def test_cloud_forge_acceleration_offline_skipped_when_disabled(monkeypatch):
    monkeypatch.delenv("UGR_ACCELERATION_TOKENS_ENABLED", raising=False)
    hammer = importlib.import_module("tools.stress.chaos_hammer")
    notes = hammer.hammer_cloud_forge_acceleration_offline()
    assert len(notes) == 1
    assert notes[0].startswith("acceleration_tokens_disabled")


def test_cloud_forge_acceleration_offline_invariants(monkeypatch, tmp_path):
    monkeypatch.setenv("UGR_ACCELERATION_TOKENS_ENABLED", "1")
    runtime_dir = str(tmp_path / "runtime")
    hammer = importlib.import_module("tools.stress.chaos_hammer")
    notes = hammer.hammer_cloud_forge_acceleration_offline(runtime_dir=runtime_dir)
    assert notes
    assert notes[-1] == "cloud_forge acceleration OFFLINE invariants hold"
    assert any("1x clamp" in n for n in notes)
    assert any("500x" in n for n in notes)
    accel_root = tmp_path / "runtime" / "ugr" / "acceleration"
    assert accel_root.is_dir()


def test_gossip_fingerprint_ignores_volatile_poll_timestamps():
    mod = _mod()
    base = {
        "mesh_ready": True,
        "peers": [{"url": "http://127.0.0.1:5000", "ok": True}],
        "polled_at_utc": "2026-06-09T12:00:00Z",
        "latency_ms": 12,
    }
    shifted = {**base, "polled_at_utc": "2026-06-09T12:00:01Z", "latency_ms": 48}
    assert mod._gossip_fingerprint(json.dumps(base)) == mod._gossip_fingerprint(json.dumps(shifted))

    structural = {**base, "peers": [{"url": "http://127.0.0.1:5001", "ok": False}]}
    assert mod._gossip_fingerprint(json.dumps(base)) != mod._gossip_fingerprint(json.dumps(structural))


def test_stable_fingerprint_ignores_ephemeral_drift_id():
    mod = _mod()
    base = {
        "charter_surfaces": {
            "epistemic_perimeter": {
                "ambiguity_signals": [
                    {
                        "drift_id": "nfdrift_2181ae90bdf4",
                        "severity": "attention",
                        "summary": "insufficient evidence",
                    }
                ]
            }
        },
        "adopted_treaties": [],
    }
    shifted = {
        **base,
        "charter_surfaces": {
            "epistemic_perimeter": {
                "ambiguity_signals": [
                    {
                        "drift_id": "nfdrift_34555f83e2d1",
                        "severity": "attention",
                        "summary": "insufficient evidence",
                    }
                ]
            }
        },
    }
    assert mod._stable_fingerprint(json.dumps(base)) == mod._stable_fingerprint(json.dumps(shifted))


def test_live_dishamory_smoke_when_server_up(tmp_path, monkeypatch):
    mod = _mod()
    common = importlib.import_module("tools.stress._chaos_common")

    if not common.server_reachable():
        import pytest

        pytest.skip("AAIS not reachable at AAIS_STRESS_BASE")

    artifact_dir = tmp_path / "ci-artifacts"
    artifact_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(common, "ROOT", tmp_path)

    summary = mod.run_dishamory_chaos(rounds=1, skip_ugr=False, phase="A")
    assert summary.get("fatal") is not True
    assert summary.get("server_still_healthy") is True
    assert summary.get("server_errors_5xx", 1) == 0
    assert summary.get("unexpected_failures", 1) == 0
    assert summary.get("total_probes", 0) >= 8

    report_path = artifact_dir / "dishamory_chaos_report.json"
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["summary"]["protocol"] == "DISHAMORY_100x"
