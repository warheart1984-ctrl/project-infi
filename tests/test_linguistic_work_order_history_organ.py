from src.linguistic_work_order_history_organ import build_linguistic_work_order_history_status


def test_linguistic_work_order_history_organ_status():
    status = build_linguistic_work_order_history_status()
    assert (
        status["linguistic_work_order_history_organ_version"]
        == "linguistic_work_order_history_organ.v1"
    )
    assert status["module_id"] == "AAIS-LWOH-01"
