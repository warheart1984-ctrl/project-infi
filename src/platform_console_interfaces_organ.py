"""Platform Console Interfaces Subsystem — platform UI posture."""

# Mythic: Platform Console Interfaces Organ
# Engineering: PlatformConsoleInterfacesInterface
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-PCI-01"
ORGAN_VERSION = "platform_console_interfaces_organ.v1"

_PLATFORM_PAGES = (
    "PlatformConsole.jsx",
    "PlatformMesh.jsx",
    "PlatformMarketplace.jsx",
)


def build_platform_console_interfaces_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    pages = root / "frontend" / "src" / "pages"
    present = sum(1 for name in _PLATFORM_PAGES if (pages / name).is_file())
    return {
        "platform_console_interfaces_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"platform_pages={present};read_only=1"[:128],
        "platform_pages_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
