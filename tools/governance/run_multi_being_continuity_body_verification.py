#!/usr/bin/env python3
"""Multi-being continuity body verification gate (Release 41 / Stage 10)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/MULTI_BEING_CONTINUITY_CONTRACT.md", "file"),
    ("schemas/operator_multi_being_pact.v1.json", "file"),
    ("schemas/multi_being_drift.v1.json", "file"),
    ("governance/operator_multi_being_registry.v1.json", "file"),
    ("src.multi_being_continuity_runtime", "MultiBeingContinuityRuntime"),
    ("src.multi_being_continuity_registry", "validate_multi_being_registry"),
    ("src.jarvis_multi_being_authority", "authorize_federation_slot_admission"),
    ("src.jarvis_multi_being_authority", "authorize_federation_influence"),
    ("src.multi_being_pact_adoption_bridge", "maybe_enqueue_multi_being_pact_adoption_approval"),
    ("src.multi_being_continuity_organ", "build_multi_being_continuity_status"),
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
                elif attr == "MultiBeingContinuityRuntime" and not hasattr(target, "observe_multi_being_drift"):
                    failures.append("MultiBeingContinuityRuntime.observe_multi_being_drift missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")

    from src.multi_being_continuity_registry import validate_multi_being_registry

    registry_errors = validate_multi_being_registry()
    if registry_errors:
        failures.extend([f"multi-being registry: {e}" for e in registry_errors])

    genome = ROOT / "governance/subsystem_genomes/multi_being_continuity_runtime.genome.v1.json"
    if not genome.is_file():
        failures.append("missing multi_being_continuity_runtime genome")

    proof = ROOT / "docs/proof/platform/MULTI_BEING_CONTINUITY_V1_PROOF.md"
    if not proof.is_file():
        failures.append("missing MULTI_BEING_CONTINUITY_V1_PROOF.md")

    if failures:
        print("MULTI-BEING CONTINUITY BODY GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("MULTI-BEING CONTINUITY BODY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
