from src.linguistic_governance_attestation_organ import build_linguistic_governance_attestation_status


def test_build_status():
    status = build_linguistic_governance_attestation_status()
    assert status["linguistic_governance_attestation_organ_version"] == (
        "linguistic_governance_attestation_organ.v1"
    )
    assert status["read_only"] is True
