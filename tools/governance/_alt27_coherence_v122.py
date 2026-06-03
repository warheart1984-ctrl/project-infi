#!/usr/bin/env python3
"""Bump operator_cognition_coherence_fabric schema to v1.22 for Release 27.1."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / "schemas/operator_cognition_coherence_fabric.v1.21.json"
data = json.loads(src.read_text(encoding="utf-8"))
data["$id"] = "operator_cognition_coherence_fabric.v1.22"
data["title"] = "Operator Cognition Coherence Fabric v1.22"
props = data["properties"]
props["operator_cognition_coherence_fabric_version"]["const"] = (
    "operator_cognition_coherence_fabric.v1.22"
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
    "cisiv_lineage_triangulation_layer",
    "constitutional_bridge_layer",
    "creative_trust_chain_layer",
):
    props[name] = {"type": "array", "items": layer_item}
for flag in (
    "cisiv_lineage_triangulation_aligned",
    "constitutional_bridge_aligned",
    "creative_trust_chain_aligned",
    "cisiv_early_ideas_bundle_aligned",
):
    props[flag] = {"type": "boolean"}
out = ROOT / "schemas/operator_cognition_coherence_fabric.v1.22.json"
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}")
