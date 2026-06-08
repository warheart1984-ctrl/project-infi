#!/usr/bin/env python3

"""Constitutional evolution body verification gate (Release 47 / Stage 17)."""



from __future__ import annotations



import importlib

import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



CHECKS = [

    ("docs/contracts/CONSTITUTIONAL_EVOLUTION_CONTRACT.md", "file"),

    ("schemas/operator_charter_amendment.v1.json", "file"),

    ("governance/operator_constitutional_evolution_registry.v1.json", "file"),

    ("governance/subsystem_genomes/constitutional_evolution_runtime.genome.v1.json", "file"),

    ("src.constitutional_evolution_runtime", "ConstitutionalEvolutionRuntime"),

    ("src.constitutional_evolution_registry", "validate_evolution_registry"),

    ("src.jarvis_constitutional_evolution_authority", "authorize_amendment_overlay_admission"),

    ("src.constitutional_evolution_organ", "build_constitutional_evolution_status"),

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



    from src.constitutional_evolution_registry import validate_evolution_registry



    if validate_evolution_registry():

        failures.extend([f"evolution registry: {e}" for e in validate_evolution_registry()])



    if failures:

        print("CONSTITUTIONAL EVOLUTION BODY GATE: FAIL")

        for item in failures:

            print(f"  - {item}")

        return 1

    print("CONSTITUTIONAL EVOLUTION BODY GATE: PASS")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

