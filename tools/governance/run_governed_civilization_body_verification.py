#!/usr/bin/env python3

"""Governed civilization body verification gate (Release 48 / Stage 18)."""



from __future__ import annotations



import importlib

import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



CHECKS = [

    ("docs/contracts/GOVERNED_CIVILIZATION_CONTRACT.md", "file"),

    ("schemas/operator_civilization_charter.v1.json", "file"),

    ("governance/operator_civilization_registry.v1.json", "file"),

    ("src.governed_civilization_runtime", "GovernedCivilizationRuntime"),

    ("src.governed_civilization_registry", "validate_civilization_registry"),

    ("src.jarvis_civilization_authority", "authorize_civilization_overlay_admission"),

    ("src.governed_civilization_organ", "build_governed_civilization_status"),

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



    from src.governed_civilization_registry import validate_civilization_registry



    if validate_civilization_registry():

        failures.extend([f"civilization registry: {e}" for e in validate_civilization_registry()])



    if not (ROOT / "docs/proof/platform/GOVERNED_CIVILIZATION_V1_PROOF.md").is_file():

        failures.append("missing GOVERNED_CIVILIZATION_V1_PROOF.md")



    if failures:

        print("GOVERNED CIVILIZATION BODY GATE: FAIL")

        for item in failures:

            print(f"  - {item}")

        return 1

    print("GOVERNED CIVILIZATION BODY GATE: PASS")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

