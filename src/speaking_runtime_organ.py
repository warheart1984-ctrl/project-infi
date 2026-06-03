"""Speaking Runtime Organ — read-only speaking.runtime posture."""

# Mythic: Speaking Runtime Organ
# Engineering: SpeakingRuntimeEngine
from __future__ import annotations

from typing import Any

from src.speaking_runtime import (
    SPEAKING_RUNTIME_ID,
    SPEAKING_STAGES,
    speaking_runtime_spec,
)

MODULE_ID = "AAIS-SRO-02"
ORGAN_VERSION = "speaking_runtime_organ.v1"


def build_speaking_runtime_status() -> dict[str, Any]:
    spec = speaking_runtime_spec()
    return {
        "speaking_runtime_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "runtime_id": spec.get("runtime_id") or SPEAKING_RUNTIME_ID,
        "runtime_version": str(spec.get("version") or ""),
        "stages": list(SPEAKING_STAGES),
        "summary": str(spec.get("summary") or "")[:128],
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
