from src.linguistic_full_governance_cycle_history_organ import build_linguistic_full_governance_cycle_history_status


def test_build_status():
    status = build_linguistic_full_governance_cycle_history_status()
    assert status["linguistic_full_governance_cycle_history_organ_version"] == "linguistic_full_governance_cycle_history_organ.v1"
    assert status["read_only"] is True
