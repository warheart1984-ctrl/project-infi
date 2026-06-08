#!/usr/bin/env python3
"""Governance membrane body verification gate (Release 44 / Stage 13)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/MULTI_ORGANISM_GOVERNANCE_MEMBRANE_CONTRACT.md", "file"),
    ("schemas/operator_membrane_policy.v1.json", "file"),
    ("governance/operator_membrane_registry.v1.json", "file"),
    ("src.multi_organism_governance_membrane_runtime", "MultiOrganismGovernanceMembraneRuntime"),
    ("src.multi_organism_governance_membrane_registry", "validate_membrane_registry"),
    ("src.jarvis_membrane_authority", "authorize_membrane_slot_admission"),
    ("src.imxp_governance_wrapper", "check_imxp_outbound_permeability"),
    ("src.multi_organism_governance_membrane_organ", "build_governance_membrane_status"),
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

    from src.multi_organism_governance_membrane_registry import validate_membrane_registry

    if validate_membrane_registry():
        failures.extend([f"membrane registry: {e}" for e in validate_membrane_registry()])

    if not (ROOT / "docs/proof/platform/GOVERNANCE_MEMBRANE_V1_PROOF.md").is_file():
        failures.append("missing GOVERNANCE_MEMBRANE_V1_PROOF.md")

    if failures:
        print("GOVERNANCE MEMBRANE BODY GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("GOVERNANCE MEMBRANE BODY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
