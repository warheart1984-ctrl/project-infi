#!/usr/bin/env python3
"""Culture habit verification gate (Release 36 / Stage 5)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/CULTURE_HABIT_CONTRACT.md", "file"),
    ("schemas/operator_habit.v1.json", "file"),
    ("schemas/habit_pattern.v1.json", "file"),
    ("governance/operator_habit_registry.v1.json", "file"),
    ("src.culture_habit_runtime", "CultureHabitRuntime"),
    ("src.culture_habit_registry", "validate_habit_registry"),
    ("src.jarvis_habit_authority", "authorize_habit_influence"),
    ("src.habit_adoption_bridge", "maybe_enqueue_habit_adoption_approval"),
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
                elif attr == "CultureHabitRuntime" and not hasattr(target, "mine_habit_patterns"):
                    failures.append("CultureHabitRuntime.mine_habit_patterns missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")

    from src.culture_habit_registry import validate_habit_registry

    registry_errors = validate_habit_registry()
    if registry_errors:
        failures.extend([f"habit registry: {e}" for e in registry_errors])

    genome = ROOT / "governance/subsystem_genomes/culture_habit_runtime.genome.v1.json"
    if not genome.is_file():
        failures.append("missing culture_habit_runtime genome")

    proof = ROOT / "docs/proof/platform/CULTURE_HABIT_V1_PROOF.md"
    if not proof.is_file():
        failures.append("missing CULTURE_HABIT_V1_PROOF.md")

    if failures:
        print("CULTURE HABIT GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("CULTURE HABIT GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
