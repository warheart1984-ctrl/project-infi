"""Wolf Rehydration Organ — read-only metal reboot continuity harness posture."""

# Mythic: Wolf Rehydration Organ
# Engineering: WolfRehydrationEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-WRO-01"
ORGAN_VERSION = "wolf_rehydration_organ.v1"


def build_wolf_rehydration_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    harness_present = (
        root / "src" / "cog_runtime" / "wolf_rehydration_harness.py"
    ).is_file()
    bridge_present = (root / "src" / "cogos_runtime_bridge.py").is_file()
    summary = (
        f"harness={int(harness_present)};bridge={int(bridge_present)};read_only=1"
    )[:128]
    return {
        "wolf_rehydration_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "harness_module_present": harness_present,
        "cogos_bridge_present": bridge_present,
        "cross_machine_replay": False,
        "metal_proof_scope": "single_machine_asserted",
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
