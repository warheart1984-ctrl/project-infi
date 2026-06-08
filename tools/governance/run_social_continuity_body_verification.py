#!/usr/bin/env python3
"""Social continuity body verification gate (Release 40 / Stage 9)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/SOCIAL_CONTINUITY_CONTRACT.md", "file"),
    ("schemas/operator_social_bond.v1.json", "file"),
    ("schemas/social_drift.v1.json", "file"),
    ("governance/operator_social_registry.v1.json", "file"),
    ("src.social_continuity_runtime", "SocialContinuityRuntime"),
    ("src.social_continuity_registry", "validate_social_registry"),
    ("src.jarvis_social_authority", "authorize_archive_admission"),
    ("src.jarvis_social_authority", "authorize_social_influence"),
    ("src.social_bond_adoption_bridge", "maybe_enqueue_social_bond_adoption_approval"),
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
                elif attr == "SocialContinuityRuntime" and not hasattr(target, "observe_social_drift"):
                    failures.append("SocialContinuityRuntime.observe_social_drift missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")

    from src.social_continuity_registry import validate_social_registry

    registry_errors = validate_social_registry()
    if registry_errors:
        failures.extend([f"social registry: {e}" for e in registry_errors])

    genome = ROOT / "governance/subsystem_genomes/social_continuity_runtime.genome.v1.json"
    if not genome.is_file():
        failures.append("missing social_continuity_runtime genome")

    proof = ROOT / "docs/proof/platform/SOCIAL_CONTINUITY_V1_PROOF.md"
    if not proof.is_file():
        failures.append("missing SOCIAL_CONTINUITY_V1_PROOF.md")

    if failures:
        print("SOCIAL CONTINUITY BODY GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("SOCIAL CONTINUITY BODY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
