"""CRK-1 insulation attack simulator — all vectors must PASS (blocked)."""

from __future__ import annotations

from src.crk1.attack_simulator import InsulationAttackSimulator
from src.crk1.runtime_facade import CRK1Runtime
from src.continuity.constitutional_runtime import ConstitutionalRuntime


def test_insulation_attacks_all_pass(crk1_runtime: ConstitutionalRuntime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    identity_id = crk1_runtime.ledgers.identity.id
    simulator = InsulationAttackSimulator(facade)
    report = simulator.run_all(identity_id)
    assert set(report.keys()) == {
        "drop_outcome",
        "non_replayable_outcome",
        "quarantine_evidence",
        "fork_without_history",
        "decision_without_evidence",
        "replay_bypass",
    }
    for name, (_key, result) in report.items():
        assert result == "PASS", f"{name} failed constitutional guard: {result}"
