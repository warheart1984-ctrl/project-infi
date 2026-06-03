#!/usr/bin/env python3
"""Bump operator_cognition_coherence_fabric schema to v1.18 for Release 23."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / "schemas/operator_cognition_coherence_fabric.v1.17.json"
data = json.loads(src.read_text(encoding="utf-8"))
data["$id"] = "operator_cognition_coherence_fabric.v1.18"
data["title"] = "Operator Cognition Coherence Fabric v1.18"
props = data["properties"]
props["operator_cognition_coherence_fabric_version"]["const"] = (
    "operator_cognition_coherence_fabric.v1.18"
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
    "linguistic_forecast_layer",
    "linguistic_predictive_cycle_layer",
    "linguistic_governance_cycle_layer",
):
    props[name] = {"type": "array", "items": layer_item}
for flag in (
    "linguistic_forecast_aligned",
    "linguistic_predictive_cycle_aligned",
    "linguistic_governance_cycle_aligned",
    "linguistic_closed_loop_aligned",
):
    props[flag] = {"type": "boolean"}
out = ROOT / "schemas/operator_cognition_coherence_fabric.v1.18.json"
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}")
