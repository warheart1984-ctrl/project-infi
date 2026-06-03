from src.meta_linguistic_registry_organ import build_meta_linguistic_registry_status


def test_build_status():
    status = build_meta_linguistic_registry_status()
    assert status["meta_linguistic_registry_organ_version"] == "meta_linguistic_registry_organ.v1"
    assert status["read_only"] is True
