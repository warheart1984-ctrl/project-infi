"""Attention Organ — read-only cognitive.attention lobe posture."""

# Mythic: Attention Organ
# Engineering: AttentionEngine
from __future__ import annotations

from typing import Any

from src.cog_runtime.attention import ATTENTION_RUNTIME_ID, attention_runtime_spec

MODULE_ID = "AAIS-ATO-01"
ORGAN_VERSION = "attention_organ.v1"


def build_attention_status() -> dict[str, Any]:
    spec = attention_runtime_spec()
    return {
        "attention_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "runtime_id": spec.get("runtime_id") or ATTENTION_RUNTIME_ID,
        "runtime_version": str(spec.get("version") or ""),
        "stages": list(spec.get("stages") or ()),
        "summary": str(spec.get("summary") or "")[:128],
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
