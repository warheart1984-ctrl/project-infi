from src.linguistic_full_governance_cycle_organ import build_linguistic_full_governance_cycle_status


def test_build_status():
    status = build_linguistic_full_governance_cycle_status()
    assert status["linguistic_full_governance_cycle_organ_version"] == (
        "linguistic_full_governance_cycle_organ.v1"
    )
    assert status["read_only"] is True
