"""Cloud Forge failsafe probes (Phase 1)."""

from __future__ import annotations

import os
from pathlib import Path

FORCE_SAFE_ENV = "CLOUD_FORGE_FORCE_SAFE"
FORCE_SAFE_FLAG = Path(".runtime/cloud_forge/force_safe")


def failsafe_force_safe() -> bool:
    """True when global FORCE_SAFE is active per failsafe doc."""
    if os.environ.get(FORCE_SAFE_ENV, "").strip() in {"1", "true", "yes"}:
        return True
    try:
        return FORCE_SAFE_FLAG.is_file()
    except OSError:
        return False
