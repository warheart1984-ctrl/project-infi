#!/usr/bin/env python3
"""Autobiographical agency body verification gate (Release 39 / Stage 8)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/AUTOBIOGRAPHICAL_AGENCY_CONTRACT.md", "file"),
    ("schemas/operator_autobiographical_episode.v1.json", "file"),
    ("schemas/autobiographical_drift.v1.json", "file"),
    ("governance/operator_autobiographical_registry.v1.json", "file"),
    ("src.autobiographical_agency_runtime", "AutobiographicalAgencyRuntime"),
    ("src.autobiographical_agency_registry", "validate_autobiographical_registry"),
    ("src.jarvis_autobiographical_authority", "authorize_operational_admission"),
    ("src.jarvis_autobiographical_authority", "authorize_agency_influence"),
    ("src.autobiographical_episode_adoption_bridge", "maybe_enqueue_autobiographical_episode_adoption_approval"),
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
                elif attr == "AutobiographicalAgencyRuntime" and not hasattr(
                    target, "observe_autobiographical_drift"
                ):
                    failures.append("AutobiographicalAgencyRuntime.observe_autobiographical_drift missing")
            except Exception as exc:
                failures.append(f"{module_name}: {exc}")

    from src.autobiographical_agency_registry import validate_autobiographical_registry

    registry_errors = validate_autobiographical_registry()
    if registry_errors:
        failures.extend([f"autobiographical registry: {e}" for e in registry_errors])

    genome = ROOT / "governance/subsystem_genomes/autobiographical_agency_runtime.genome.v1.json"
    if not genome.is_file():
        failures.append("missing autobiographical_agency_runtime genome")

    proof = ROOT / "docs/proof/platform/AUTOBIOGRAPHICAL_AGENCY_V1_PROOF.md"
    if not proof.is_file():
        failures.append("missing AUTOBIOGRAPHICAL_AGENCY_V1_PROOF.md")

    if failures:
        print("AUTOBIOGRAPHICAL AGENCY BODY GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("AUTOBIOGRAPHICAL AGENCY BODY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
