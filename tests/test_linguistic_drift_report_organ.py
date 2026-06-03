from src.linguistic_drift_report_organ import build_linguistic_drift_report_status


def test_build_status():
    status = build_linguistic_drift_report_status()
    assert status["linguistic_drift_report_organ_version"] == "linguistic_drift_report_organ.v1"
    assert status["read_only"] is True
