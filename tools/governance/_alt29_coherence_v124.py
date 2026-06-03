#!/usr/bin/env python3
"""Bump operator_cognition_coherence_fabric schema to v1.24 for Release 29."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / "schemas/operator_cognition_coherence_fabric.v1.23.json"
data = json.loads(src.read_text(encoding="utf-8"))
data["$id"] = "operator_cognition_coherence_fabric.v1.24"
data["title"] = "Operator Cognition Coherence Fabric v1.24"
props = data["properties"]
props["operator_cognition_coherence_fabric_version"]["const"] = (
    "operator_cognition_coherence_fabric.v1.24"
)
layer_item = props["story_forge_expansion_layer"]["items"]
props["story_forge_execution_layer"] = {"type": "array", "items": layer_item}
for flag in (
    "story_forge_execution_aligned",
    "story_forge_execution_bundle_aligned",
    "memory_governance_universal_aligned",
    "capability_bridge_universal_aligned",
    "pipeline_transport_aligned",
    "perception_router_aligned",
    "integration_universal_bundle_aligned",
):
    props[flag] = {"type": "boolean"}
out = ROOT / "schemas/operator_cognition_coherence_fabric.v1.24.json"
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}")
