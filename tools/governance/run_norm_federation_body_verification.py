#!/usr/bin/env python3

"""Norm federation body verification gate (Release 46 / Stage 16)."""



from __future__ import annotations



import importlib

import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



CHECKS = [

    ("docs/contracts/NORM_FEDERATION_CONTRACT.md", "file"),

    ("schemas/operator_norm_federation_treaty.v1.json", "file"),

    ("governance/operator_norm_federation_registry.v1.json", "file"),

    ("src.norm_federation_runtime", "NormFederationRuntime"),

    ("src.norm_federation_registry", "validate_norm_federation_registry"),

    ("src.jarvis_norm_federation_authority", "authorize_norm_federation_overlay_admission"),

    ("src.norm_federation_organ", "build_norm_federation_status"),

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



    from src.norm_federation_registry import validate_norm_federation_registry



    if validate_norm_federation_registry():

        failures.extend([f"norm federation registry: {e}" for e in validate_norm_federation_registry()])



    if failures:

        print("NORM FEDERATION BODY GATE: FAIL")

        for item in failures:

            print(f"  - {item}")

        return 1

    print("NORM FEDERATION BODY GATE: PASS")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

