from src.linguistic_governed_lifecycle_fabric_organ import build_linguistic_governed_lifecycle_fabric_status


def test_build_status():
    status = build_linguistic_governed_lifecycle_fabric_status()
    assert status["linguistic_governed_lifecycle_fabric_organ_version"] == "linguistic_governed_lifecycle_fabric_organ.v1"
    assert status["read_only"] is True
