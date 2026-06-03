"""Nova Workspace Interface Subsystem — Nova/Jarvis page posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-NWI-01"
ORGAN_VERSION = "nova_workspace_interface_organ.v1"

_PAGES = ("NovaPage.jsx", "JarvisPage.jsx")


def build_nova_workspace_interface_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    pages = root / "frontend" / "src" / "pages"
    present = sum(1 for name in _PAGES if (pages / name).is_file())
    return {
        "nova_workspace_interface_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"nova_workspace_pages={present};read_only=1"[:128],
        "nova_workspace_pages_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
