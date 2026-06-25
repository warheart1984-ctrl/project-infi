#!/usr/bin/env python3

"""Inter-substrate diplomacy body verification gate (Release 45 / Stage 15)."""



from __future__ import annotations



import importlib

import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



CHECKS = [

    ("docs/contracts/INTER_SUBSTRATE_DIPLOMACY_CONTRACT.md", "file"),

    ("schemas/operator_diplomatic_accord.v1.json", "file"),

    ("governance/operator_diplomatic_registry.v1.json", "file"),

    ("src.diplomacy.runtime", "InterSubstrateDiplomacyRuntime"),

    ("src.diplomacy.registry", "validate_diplomatic_registry"),

    ("src.jarvis_diplomacy_authority", "authorize_diplomacy_overlay_admission"),

    ("src.diplomatic_accord_adoption_bridge", "enqueue_diplomatic_accord_adoption"),

    ("src.diplomacy.organ", "build_inter_substrate_diplomacy_status"),

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



    from src.diplomacy.registry import validate_diplomatic_registry



    if validate_diplomatic_registry():

        failures.extend([f"diplomatic registry: {e}" for e in validate_diplomatic_registry()])



    if failures:

        print("INTER-SUBSTRATE DIPLOMACY BODY GATE: FAIL")

        for item in failures:

            print(f"  - {item}")

        return 1

    print("INTER-SUBSTRATE DIPLOMACY BODY GATE: PASS")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

