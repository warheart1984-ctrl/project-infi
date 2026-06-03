"""CoGOS Runtime Bridge Organ — read-only family bridge posture."""

# Mythic: Cogos Runtime Bridge Organ
# Engineering: CogosRuntimeBridgeBridge
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.cogos_runtime_bridge import family_spec, validate_family_config

MODULE_ID = "AAIS-CRB-01"
ORGAN_VERSION = "cogos_runtime_bridge_organ.v1"


def build_cogos_runtime_bridge_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    spec = family_spec()
    validation = validate_family_config(spec)
    default_family_path = Path("/opt/cogos/config/cognitive_runtime_family.json")
    payload_family = root / "wolf-cog-os" / "payload" / "opt" / "cogos" / "config" / "cognitive_runtime_family.json"
    summary = (
        f"family={spec.get('family_id')};valid={int(validation.get('valid'))};"
        f"payload={int(payload_family.is_file())}"
    )[:128]
    return {
        "cogos_runtime_bridge_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "family_id": spec.get("family_id"),
        "family_valid": bool(validation.get("valid")),
        "validation_issues": list(validation.get("issues") or [])[:8],
        "default_family_path": str(default_family_path),
        "payload_family_present": payload_family.is_file(),
        "rehydrate_boot_supported": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
