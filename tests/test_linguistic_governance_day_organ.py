from src.linguistic_governance_day_organ import build_linguistic_governance_day_status


def test_linguistic_governance_day_organ_status():
    status = build_linguistic_governance_day_status()
    assert status["linguistic_governance_day_organ_version"] == "linguistic_governance_day_organ.v1"
    assert status["module_id"] == "AAIS-LGD-01"
    assert status["day_engine_present"] is True
