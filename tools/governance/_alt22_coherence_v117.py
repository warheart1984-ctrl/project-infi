#!/usr/bin/env python3
"""Bump operator_cognition_coherence_fabric schema to v1.17 for Release 22."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / "schemas/operator_cognition_coherence_fabric.v1.16.json"
data = json.loads(src.read_text(encoding="utf-8"))
data["$id"] = "operator_cognition_coherence_fabric.v1.17"
data["title"] = "Operator Cognition Coherence Fabric v1.17"
props = data["properties"]
props["operator_cognition_coherence_fabric_version"]["const"] = (
    "operator_cognition_coherence_fabric.v1.17"
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
    "naming_protocol_layer",
    "linguistic_mutation_layer",
    "meta_linguistic_orchestration_layer",
):
    props[name] = {"type": "array", "items": layer_item}
for flag in (
    "naming_protocol_aligned",
    "linguistic_mutation_aligned",
    "meta_linguistic_orchestration_aligned",
    "meta_linguistic_governance_aligned",
):
    props[flag] = {"type": "boolean"}
out = ROOT / "schemas/operator_cognition_coherence_fabric.v1.17.json"
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}")
