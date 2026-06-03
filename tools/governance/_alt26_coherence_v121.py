#!/usr/bin/env python3
"""Bump operator_cognition_coherence_fabric schema to v1.21 for Release 26.1."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / "schemas/operator_cognition_coherence_fabric.v1.20.json"
data = json.loads(src.read_text(encoding="utf-8"))
data["$id"] = "operator_cognition_coherence_fabric.v1.21"
data["title"] = "Operator Cognition Coherence Fabric v1.21"
props = data["properties"]
props["operator_cognition_coherence_fabric_version"]["const"] = (
    "operator_cognition_coherence_fabric.v1.21"
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
    "linguistic_operator_day_layer",
    "linguistic_retention_history_layer",
):
    props[name] = {"type": "array", "items": layer_item}
for flag in (
    "linguistic_operator_day_aligned",
    "linguistic_retention_history_aligned",
    "linguistic_enforcement_ready",
    "linguistic_operational_closure_aligned",
):
    props[flag] = {"type": "boolean"}
out = ROOT / "schemas/operator_cognition_coherence_fabric.v1.21.json"
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}")
