"""Process-wide Constitutional State Runtime for URG missions."""

from __future__ import annotations

import os
from pathlib import Path

from constitutional.runtime import ConstitutionalStateRuntime


def urg_persist_root() -> Path:
    runtime_dir = os.getenv("AAIS_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir) / "constitutional" / "ugr"
    return Path(".runtime") / "constitutional" / "ugr"


CSR = ConstitutionalStateRuntime(persist_root=urg_persist_root())
