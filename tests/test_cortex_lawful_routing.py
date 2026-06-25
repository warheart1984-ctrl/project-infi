"""Cortex lawful routing tests."""

from __future__ import annotations

from nova.cortex.execution import CortexExecutor
from nova.cortex.router import CortexRouter
from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(id="t5-ctx", hash="ref-ctx", issued_at="now", issuer="test")


def test_all_cortex_paths_use_lawful_router(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)

    executor = CortexExecutor()
    result = executor.handle(
        kind="ACT",
        payload={"capability": "echo", "message": "hello"},
        actor_id="session-1",
        domain="substrate",
        epoch="EPOCH:5:T0",
        lineage_contract_id="lc-1",
    )

    assert result.law_result["admitted"] is True
    assert executor.router.router.evaluations
    assert executor.router.router.lineage.list()


def test_pit_band_activation_from_cortex_intents(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)

    router = CortexRouter(make_law_kernel_stack())
    result = router.handle(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.9,
            "correctness_score": 0.9,
            "message": "reflect",
        },
        actor_id="session-2",
        domain="cognition",
        epoch="EPOCH:5:T1",
        lineage_contract_id="lc-1",
    )

    assert result["action"] == "PIT-2"
    assert result["admitted"] is True
    evaluation = result["evaluation"]
    transformed = evaluation.get("transformed_intent")
    assert transformed
    assert "self_reflection" in transformed["payload"]
