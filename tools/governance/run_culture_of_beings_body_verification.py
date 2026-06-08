#!/usr/bin/env python3
"""Culture-of-beings body verification gate (Release 42 / Stage 11)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/CULTURE_OF_BEINGS_CONTRACT.md", "file"),
    ("schemas/operator_shared_norm.v1.json", "file"),
    ("schemas/culture_of_beings_drift.v1.json", "file"),
    ("governance/operator_culture_of_beings_registry.v1.json", "file"),
    ("src.culture_of_beings_runtime", "CultureOfBeingsRuntime"),
    ("src.culture_of_beings_registry", "validate_culture_of_beings_registry"),
    ("src.jarvis_culture_of_beings_authority", "authorize_culture_of_beings_slot_admission"),
    ("src.shared_norm_adoption_bridge", "maybe_enqueue_shared_norm_adoption_approval"),
    ("src.culture_of_beings_organ", "build_culture_of_beings_status"),
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
                elif attr == "CultureOfBeingsRuntime" and not hasattr(target, "observe_culture_of_beings_drift"):
                    failures.append("CultureOfBeingsRuntime.observe_culture_of_beings_drift missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")

    from src.culture_of_beings_registry import validate_culture_of_beings_registry

    if validate_culture_of_beings_registry():
        failures.extend([f"culture-of-beings registry: {e}" for e in validate_culture_of_beings_registry()])

    if not (ROOT / "governance/subsystem_genomes/culture_of_beings_runtime.genome.v1.json").is_file():
        failures.append("missing culture_of_beings_runtime genome")
    if not (ROOT / "docs/proof/platform/CULTURE_OF_BEINGS_V1_PROOF.md").is_file():
        failures.append("missing CULTURE_OF_BEINGS_V1_PROOF.md")

    if failures:
        print("CULTURE-OF-BEINGS BODY GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("CULTURE-OF-BEINGS BODY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
