#!/usr/bin/env python3
"""Body Completeness Program verification gate."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("src.otem.store", "substrate_db_enabled"),
    ("src.workflow_family_readiness", "list_families_with_readiness"),
    ("src.operator_somatic_health", "build_somatic_health_snapshot"),
    ("src.otem_autonomic_routines", "load_routines_registry"),
    ("src.immune_policy_enrollment", "build_policy_enrollment_status"),
    ("src.nova_touch_admission", "admit_touch_event"),
    ("src.nova_touch_admission", "build_nova_touch_admission_status"),
]


def main() -> int:
    failures: list[str] = []
    matrix = ROOT / "docs/runtime/AAIS_BODY_COMPLETENESS_MATRIX.md"
    if not matrix.is_file():
        failures.append("missing AAIS_BODY_COMPLETENESS_MATRIX.md")
    for module_name, attr in CHECKS:
        try:
            module = importlib.import_module(module_name)
            if not hasattr(module, attr):
                failures.append(f"{module_name}.{attr} missing")
        except Exception as exc:
            failures.append(f"{module_name}: {exc}")
    governance = ROOT / "governance/otem_autonomic_routines.v1.json"
    if not governance.is_file():
        failures.append("missing otem_autonomic_routines.v1.json")
    touch_schema = ROOT / "schemas/nova_touch_event.v1.json"
    if not touch_schema.is_file():
        failures.append("missing nova_touch_event.v1.json")
    if failures:
        print("BODY COMPLETENESS GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("BODY COMPLETENESS GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
