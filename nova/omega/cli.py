from __future__ import annotations

import json
import sys

from nova.omega.cases import all_cases, restore_ladders
from nova.omega.harness import OmegaRunner


class _DummyMonkeypatch:
    def setattr(self, path: str, value: object) -> None:
        import importlib

        module_path, attr = path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        setattr(module, attr, value)


def run_omega(threshold: float = 0.95) -> dict:
    runner = OmegaRunner(cases=all_cases())
    result = runner.run(monkeypatch=_DummyMonkeypatch())
    restore_ladders()
    result["threshold"] = threshold
    result["passed_gate"] = result["omega_score"] >= threshold
    return result


def main() -> None:
    result = run_omega()
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    if not result["passed_gate"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
