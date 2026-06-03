"""Meta-Linguistic Registry Subsystem — registry artifact hub posture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MLR-01"
ORGAN_VERSION = "meta_linguistic_registry_organ.v1"


def build_meta_linguistic_registry_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    reg_path = root / "governance" / "meta_linguistic_registry.v1.json"
    present = reg_path.is_file()
    policy_mode = "observe"
    pointer_count = 0
    if present:
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        policy_mode = reg.get("policy_mode", "observe")
        keys = (
            "last_drift_report",
            "last_forecast_report",
            "last_calibration_report",
            "last_governance_queue",
            "last_full_cycle_report",
            "last_attestation_report",
            "last_work_order_sync_at",
        )
        pointer_count = sum(1 for k in keys if reg.get(k))
    return {
        "meta_linguistic_registry_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"registry={int(present)};pointers={pointer_count}"[:128],
        "registry_present": present,
        "policy_mode": policy_mode,
        "lifecycle_pointer_count": pointer_count,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
