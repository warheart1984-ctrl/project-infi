from src.linguistic_forecast_archive_organ import build_linguistic_forecast_archive_status


def test_build_status():
    status = build_linguistic_forecast_archive_status()
    assert status["linguistic_forecast_archive_organ_version"] == "linguistic_forecast_archive_organ.v1"
    assert status["read_only"] is True
