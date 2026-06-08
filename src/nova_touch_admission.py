"""Nova touch admission — maps touch events to keystroke-equivalent turns (Release 34)."""

# Mythic: Nova Touch Admission
# Engineering: NovaTouchAdmissionEngine
from __future__ import annotations

from typing import Any

TOUCH_ADMISSION_VERSION = "nova_touch_admission.v1"
ALLOWED_TOUCH_KINDS = {"tap", "swipe", "long_press", "gesture_stub"}


def admit_touch_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize touch envelope; never persists biometrics by default."""
    touch_kind = str(payload.get("touch_kind") or "").strip().lower()
    session_id = str(payload.get("session_id") or "").strip()
    if touch_kind not in ALLOWED_TOUCH_KINDS:
        return {"ok": False, "error": "invalid touch_kind", "admitted": False}
    if not session_id:
        return {"ok": False, "error": "session_id required", "admitted": False}

    maps_to = str(payload.get("maps_to_message") or "").strip()
    if not maps_to:
        maps_to = f"[touch:{touch_kind}] operator gesture on {payload.get('target') or 'nova_surface'}"

    return {
        "ok": True,
        "admitted": True,
        "admission_version": TOUCH_ADMISSION_VERSION,
        "touch_kind": touch_kind,
        "session_id": session_id,
        "ephemeral": True,
        "logs_biometric_traces": False,
        "keystroke_equivalent": {
            "message": maps_to,
            "response_mode": "companion",
            "source": "nova_touch_admission",
        },
        "perception_gateway": {
            "route_status": "admitted_keystroke_equivalent",
            "gesture_classification": "stub",
        },
        "claim_label": "asserted",
    }


def build_nova_touch_admission_status() -> dict[str, Any]:
    return {
        "nova_touch_admission_version": TOUCH_ADMISSION_VERSION,
        "live": True,
        "persistent_storage": False,
        "allowed_touch_kinds": sorted(ALLOWED_TOUCH_KINDS),
        "read_only_posture": False,
        "claim_label": "asserted",
    }
