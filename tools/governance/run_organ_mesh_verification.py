#!/usr/bin/env python3
"""Organ mesh verification gate (Release 35 / Stage 4)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/ORGAN_COORDINATION_CONTRACT.md", "file"),
    ("schemas/organ_handoff.v1.json", "file"),
    ("schemas/organ_mesh_run.v1.json", "file"),
    ("src.organ_coordination_runtime", "OrganCoordinationRuntime"),
    ("src.jarvis_organ_mesh_authority", "authorize_mesh_run"),
    ("src.organ_mesh_approval_bridge", "maybe_enqueue_organ_mesh_approval"),
    ("src.workflow_family_registry", "validate_handoff_graph"),
]

GENOMES = [
    "workflow_family_knowledge",
    "workflow_family_business",
    "workflow_family_creative",
    "workflow_family_data",
    "workflow_family_ops",
    "workflow_family_personal",
]


def main() -> int:
    failures: list[str] = []
    for path_spec, kind in CHECKS:
        if kind == "file":
            if not (ROOT / path_spec).is_file():
                failures.append(f"missing {path_spec}")
        else:
            module_name, attr = path_spec, kind
            try:
                module = importlib.import_module(module_name)
                target = getattr(module, attr, None)
                if target is None:
                    failures.append(f"{module_name}.{attr} missing")
                elif attr == "OrganCoordinationRuntime" and not hasattr(target, "plan_mesh_run"):
                    failures.append("OrganCoordinationRuntime.plan_mesh_run missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")

    from src.workflow_family_registry import validate_handoff_graph

    graph_errors = validate_handoff_graph()
    if graph_errors:
        failures.extend([f"handoff graph: {e}" for e in graph_errors])

    for gene in GENOMES:
        genome_path = ROOT / f"governance/subsystem_genomes/{gene}.genome.v1.json"
        if not genome_path.is_file():
            failures.append(f"missing genome {gene}")

    proof = ROOT / "docs/proof/platform/ORGAN_MESH_V1_PROOF.md"
    if not proof.is_file():
        failures.append("missing ORGAN_MESH_V1_PROOF.md")

    if failures:
        print("ORGAN MESH GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("ORGAN MESH GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
