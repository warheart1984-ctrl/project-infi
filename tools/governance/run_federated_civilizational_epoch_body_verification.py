#!/usr/bin/env python3

"""Federated civilizational epoch body verification gate (Release 49 / Stage 19)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ("docs/contracts/FEDERATED_CIVILIZATIONAL_EPOCH_CONTRACT.md", "file"),
    ("docs/contracts/PEER_SUBSTRATE_FEDERATION_CONTRACT.md", "file"),
    ("schemas/operator_federated_epoch_charter.v1.json", "file"),
    ("governance/operator_federated_epoch_registry.v1.json", "file"),
    ("src.federated_civilizational_epoch_runtime", "FederatedCivilizationalEpochRuntime"),
    ("src.federated_civilizational_epoch_registry", "validate_federated_epoch_registry"),
    ("src.jarvis_federated_epoch_authority", "authorize_federated_epoch_overlay_admission"),
    ("src.federated_civilizational_epoch_organ", "build_federated_civilizational_epoch_status"),
    ("src.peer_substrate_client", "observe_all_peers"),
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

    from src.federated_civilizational_epoch_registry import validate_federated_epoch_registry

    reg_errors = validate_federated_epoch_registry(repo_root=ROOT)
    if reg_errors:
        failures.extend([f"federated epoch registry: {e}" for e in reg_errors])

    if not (ROOT / "docs/proof/platform/FEDERATED_CIVILIZATIONAL_EPOCH_V1_PROOF.md").is_file():
        failures.append("missing FEDERATED_CIVILIZATIONAL_EPOCH_V1_PROOF.md")

    if failures:
        print("FEDERATED CIVILIZATIONAL EPOCH BODY GATE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("FEDERATED CIVILIZATIONAL EPOCH BODY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
