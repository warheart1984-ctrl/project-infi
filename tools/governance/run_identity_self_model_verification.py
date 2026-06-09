#!/usr/bin/env python3
"""Identity self-model verification gate (Release 37 / Stage 6)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/IDENTITY_SELF_MODEL_CONTRACT.md", "file"),
    ("schemas/operator_identity_claim.v1.json", "file"),
    ("schemas/identity_drift.v1.json", "file"),
    ("governance/operator_identity_registry.v1.json", "file"),
    ("src.identity_self_model_runtime", "IdentitySelfModelRuntime"),
    ("src.identity_self_model_registry", "validate_identity_registry"),
    ("src.jarvis_identity_authority", "authorize_foundation_admission"),
    ("src.jarvis_identity_authority", "authorize_identity_influence"),
    ("src.identity_claim_adoption_bridge", "maybe_enqueue_identity_claim_adoption_approval"),
]


def main() -> int:
    failures: list[str] = []
    seen_modules: set[str] = set()
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
                elif attr == "IdentitySelfModelRuntime" and not hasattr(target, "observe_identity_drift"):
                    failures.append("IdentitySelfModelRuntime.observe_identity_drift missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")
            seen_modules.add(module_name)

    from src.identity_self_model_registry import validate_identity_registry

    registry_errors = validate_identity_registry()
    if registry_errors:
        failures.extend([f"identity registry: {e}" for e in registry_errors])

    genome = ROOT / "governance/subsystem_genomes/identity_self_model_runtime.genome.v1.json"
    if not genome.is_file():
        failures.append("missing identity_self_model_runtime genome")

    proof = ROOT / "docs/proof/platform/IDENTITY_SELF_MODEL_V1_PROOF.md"
    if not proof.is_file():
        failures.append("missing IDENTITY_SELF_MODEL_V1_PROOF.md")

    if failures:
        print("IDENTITY SELF-MODEL GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("IDENTITY SELF-MODEL GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
