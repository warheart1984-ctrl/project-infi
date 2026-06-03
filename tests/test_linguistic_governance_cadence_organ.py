from src.linguistic_governance_cadence_organ import build_linguistic_governance_cadence_status


def test_build_status():
    status = build_linguistic_governance_cadence_status()
    assert status["linguistic_governance_cadence_organ_version"] == "linguistic_governance_cadence_organ.v1"
    assert status["read_only"] is True
