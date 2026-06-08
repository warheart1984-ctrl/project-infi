#!/usr/bin/env python3
"""Narrative continuity body verification gate (Release 38 / Stage 7)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/NARRATIVE_CONTINUITY_CONTRACT.md", "file"),
    ("schemas/operator_narrative_beat.v1.json", "file"),
    ("schemas/narrative_drift.v1.json", "file"),
    ("governance/operator_narrative_registry.v1.json", "file"),
    ("src.narrative_continuity_runtime", "NarrativeContinuityRuntime"),
    ("src.narrative_continuity_registry", "validate_narrative_registry"),
    ("src.jarvis_narrative_authority", "authorize_session_admission"),
    ("src.jarvis_narrative_authority", "authorize_narrative_influence"),
    ("src.narrative_beat_adoption_bridge", "maybe_enqueue_narrative_beat_adoption_approval"),
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
                elif attr == "NarrativeContinuityRuntime" and not hasattr(target, "observe_narrative_drift"):
                    failures.append("NarrativeContinuityRuntime.observe_narrative_drift missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")

    from src.narrative_continuity_registry import validate_narrative_registry

    registry_errors = validate_narrative_registry()
    if registry_errors:
        failures.extend([f"narrative registry: {e}" for e in registry_errors])

    genome = ROOT / "governance/subsystem_genomes/narrative_continuity_runtime.genome.v1.json"
    if not genome.is_file():
        failures.append("missing narrative_continuity_runtime genome")

    proof = ROOT / "docs/proof/platform/NARRATIVE_CONTINUITY_V1_PROOF.md"
    if not proof.is_file():
        failures.append("missing NARRATIVE_CONTINUITY_V1_PROOF.md")

    if failures:
        print("NARRATIVE CONTINUITY BODY GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("NARRATIVE CONTINUITY BODY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
