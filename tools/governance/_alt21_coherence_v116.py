#!/usr/bin/env python3
"""Bump operator_cognition_coherence_fabric schema to v1.16 for Release 21."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / "schemas/operator_cognition_coherence_fabric.v1.15.json"
data = json.loads(src.read_text(encoding="utf-8"))
data["$id"] = "operator_cognition_coherence_fabric.v1.16"
data["title"] = "Operator Cognition Coherence Fabric v1.16"
props = data["properties"]
props["operator_cognition_coherence_fabric_version"]["const"] = (
    "operator_cognition_coherence_fabric.v1.16"
)
layer_item = {
    "type": "object",
    "required": ["organ_id", "stage", "claim_label"],
    "properties": {
        "organ_id": {"type": "string"},
        "stage": {"type": "string"},
        "claim_label": {"type": "string"},
        "read_only": {"type": "boolean"},
    },
    "additionalProperties": True,
}
for name in (
    "creative_core_layer",
    "v9_creative_layer",
    "v10_creative_layer",
):
    props[name] = {"type": "array", "items": layer_item}
for flag in (
    "creative_core_aligned",
    "v9_creative_aligned",
    "v10_creative_aligned",
    "creative_runtime_v9_v10_aligned",
):
    props[flag] = {"type": "boolean"}
out = ROOT / "schemas/operator_cognition_coherence_fabric.v1.16.json"
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}")
