"""Capability Module Organ — read-only capability module layer over service bridge."""

# Mythic: Capability Module Organ
# Engineering: CapabilityModuleEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CM-01"
ORGAN_VERSION = "capability_module_organ.v1"

# Paths not yet routed through capability_service_bridge (documented gaps).
BRIDGE_GAP_PATHS = (
    "memory",
    "workspace",
    "action",
    "forge",
)


def build_capability_module_status(*, root: Path | None = None) -> dict[str, Any]:
    """Capability module posture with universal-bridge gap map."""
    root = root or Path(__file__).resolve().parents[1]
    module_py = (root / "src" / "capability_module.py").is_file()
    bridge_py = (root / "src" / "capability_service_bridge.py").is_file()
    phase_gate_py = (root / "src" / "phase_gate.py").is_file()
    universal_bridge = False
    gap_paths: list[str] = list(BRIDGE_GAP_PATHS)
    try:
        from src.jarvis_operator import jarvis_operator
        from src.capability_bridge_universal import universal_bridge_enforced

        universal_bridge = universal_bridge_enforced(jarvis_operator.capability_bridge)
        if universal_bridge:
            gap_paths = []
    except Exception:
        pass
    summary = (
        f"module={module_py};bridge={bridge_py};"
        f"gaps={len(gap_paths)};universal={universal_bridge}"
    )[:128]
    return {
        "capability_module_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "capability_module_present": module_py,
        "service_bridge_present": bridge_py,
        "phase_gate_present": phase_gate_py,
        "universal_bridge_enforced": universal_bridge,
        "bridge_gap_paths": gap_paths,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
