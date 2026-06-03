from src.linguistic_subsystem_promotion_organ import build_linguistic_subsystem_promotion_status


def test_build_status():
    status = build_linguistic_subsystem_promotion_status()
    assert status["linguistic_subsystem_promotion_organ_version"] == "linguistic_subsystem_promotion_organ.v1"
    assert status["read_only"] is True
