"""Wave 6 transition seam invariants — legacy mount + dual-path chat."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEAMS = ROOT / "docs" / "contracts" / "seams"


def test_transition_seam_records_exist():
    assert (SEAMS / "SEAM-TRANSITION-001-legacy-api-mount.md").is_file()
    assert (SEAMS / "SEAM-TRANSITION-002-dual-path-chat.md").is_file()


def test_chat_routing_contract_exists():
    assert (ROOT / "docs" / "contracts" / "AAIS_CHAT_ROUTING_CONTRACT.md").is_file()


def test_legacy_bridge_module_exports_mount_path():
    from app.main import LEGACY_API_MOUNT_PATH, legacy_api_bridge

    assert LEGACY_API_MOUNT_PATH == "/legacy_api"
    assert hasattr(legacy_api_bridge, "loaded")


def test_health_payload_shape_documents_legacy_invariants():
    from app.main import _build_operator_health_payload

    payload = _build_operator_health_payload()
    assert "legacy_api_loaded" in payload
    assert "legacy_api_mount_error" in payload
