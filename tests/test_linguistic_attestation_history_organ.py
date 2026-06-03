from src.linguistic_attestation_history_organ import build_linguistic_attestation_history_status


def test_linguistic_attestation_history_organ_status():
    status = build_linguistic_attestation_history_status()
    assert (
        status["linguistic_attestation_history_organ_version"]
        == "linguistic_attestation_history_organ.v1"
    )
    assert status["module_id"] == "AAIS-LAH-01"
