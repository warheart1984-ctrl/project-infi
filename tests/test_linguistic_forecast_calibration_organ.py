from src.linguistic_forecast_calibration_organ import build_linguistic_forecast_calibration_status


def test_build_status():
    status = build_linguistic_forecast_calibration_status()
    assert status["linguistic_forecast_calibration_organ_version"] == (
        "linguistic_forecast_calibration_organ.v1"
    )
    assert status["read_only"] is True
    assert status["module_id"] == "AAIS-LFC-02"
