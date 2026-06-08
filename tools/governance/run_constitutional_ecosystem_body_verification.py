#!/usr/bin/env python3
"""Constitutional ecosystem body verification gate (Release 43 / Stage 12)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/CONSTITUTIONAL_ECOSYSTEM_CONTRACT.md", "file"),
    ("schemas/operator_ecosystem_charter.v1.json", "file"),
    ("governance/operator_ecosystem_registry.v1.json", "file"),
    ("src.constitutional_ecosystem_runtime", "ConstitutionalEcosystemRuntime"),
    ("src.constitutional_ecosystem_registry", "validate_ecosystem_registry"),
    ("src.jarvis_ecosystem_authority", "authorize_ecosystem_slot_admission"),
    ("src.constitutional_ecosystem_organ", "build_constitutional_ecosystem_status"),
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
                if getattr(module, attr, None) is None:
                    failures.append(f"{module_name}.{attr} missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")

    from src.constitutional_ecosystem_registry import validate_ecosystem_registry

    if validate_ecosystem_registry():
        failures.extend([f"ecosystem registry: {e}" for e in validate_ecosystem_registry()])

    if not (ROOT / "docs/proof/platform/CONSTITUTIONAL_ECOSYSTEM_V1_PROOF.md").is_file():
        failures.append("missing CONSTITUTIONAL_ECOSYSTEM_V1_PROOF.md")

    if failures:
        print("CONSTITUTIONAL ECOSYSTEM BODY GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("CONSTITUTIONAL ECOSYSTEM BODY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
