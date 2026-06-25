"""CRK-T4 perception health panel tests."""

from __future__ import annotations

from nova.cortex.execution import CortexExecutor
from nova.crk.cockpit.summary_builder import build_cockpit_summary
from nova.crk.panels.perception_health_panel import clear_perception_snapshots
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(id="t5-per", hash="ref-per", issued_at="now", issuer="test")


def test_perception_snapshots_replay_stable(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_perception_snapshots()

    executor = CortexExecutor()
    result = executor.handle(
        kind="ACT",
        payload={"capability": "echo", "message": "ping", "anomaly_score": 0.1},
        actor_id="user:1",
        domain="substrate",
        epoch="EPOCH:2:T0",
        lineage_contract_id="lc-1",
    )
    assert result.perception_snapshot is not None
    stable = result.perception_snapshot
    again = executor.handle(
        kind="ACT",
        payload={"capability": "echo", "message": "ping", "anomaly_score": 0.1},
        actor_id="user:1",
        domain="substrate",
        epoch="EPOCH:2:T0",
        lineage_contract_id="lc-1",
    )
    assert again.perception_snapshot["anomaly_score"] == stable["anomaly_score"]


def test_perception_health_degrades_with_anomaly(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_perception_snapshots()

    executor = CortexExecutor()
    low = executor.handle(
        kind="ACT",
        payload={"capability": "echo", "message": "ok", "force_anomaly": 0.1},
        actor_id="user:1",
        domain="substrate",
        epoch="EPOCH:2:T1",
        lineage_contract_id="lc-1",
    )
    high = executor.handle(
        kind="ACT",
        payload={"capability": "echo", "message": "bad", "force_anomaly": 0.9},
        actor_id="user:1",
        domain="substrate",
        epoch="EPOCH:2:T1",
        lineage_contract_id="lc-1",
    )

    panel = executor.perception_panel
    summary = panel.evaluate_epoch("EPOCH:2:T1")
    assert summary.latest_health == "degraded"
    assert summary.max_anomaly >= high.perception_snapshot["anomaly_score"]  # type: ignore[index]
    assert low.perception_snapshot["anomaly_score"] < high.perception_snapshot["anomaly_score"]  # type: ignore[index]


def test_cockpit_reports_perception_health_consistently(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_perception_snapshots()

    executor = CortexExecutor()
    executor.handle(
        kind="ACT",
        payload={"capability": "echo", "message": "x", "force_anomaly": 0.5},
        actor_id="user:1",
        domain="substrate",
        epoch="EPOCH:2:T2",
        lineage_contract_id="lc-1",
    )
    summary = build_cockpit_summary(epoch_id="EPOCH:2:T2")
    assert summary["perception_health"]["latest_perception_health"] == "drifting"
    assert summary["perception_health"]["anomaly_trend"]
