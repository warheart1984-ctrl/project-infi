"""Nova Landing Surface Organ — UI binding posture."""

# Mythic: Nova Landing Surface Organ
# Engineering: NovaLandingSurfaceInterface
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-NLS-01"
ORGAN_VERSION = "nova_landing_surface_organ.v1"


def build_nova_landing_surface_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "frontend" / "src" / "pages" / "NovaLandingPage.jsx").is_file()
    return {
        "nova_landing_surface_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"nova_landing_ui={int(present)};read_only=1"[:128],
        "nova_landing_surface_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
