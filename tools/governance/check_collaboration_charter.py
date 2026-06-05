#!/usr/bin/env python3
"""Human-AI Co-Collaboration Charter ingress gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

CHARTER = _ROOT / "lawbook" / "HUMAN_AI_CO_COLLABORATION_CHARTER.md"
SPEC = _ROOT / "docs" / "substrate" / "INGRESS_COLLABORATION_MEMBRANE.md"
MEMBRANE = _ROOT / "src" / "substrate" / "ingress" / "collaboration_membrane.py"


def main() -> int:
    errors: list[str] = []
    for path in (CHARTER, SPEC, MEMBRANE):
        if not path.is_file():
            errors.append(f"missing: {path.relative_to(_ROOT)}")

    if not errors:
        from src.substrate.ingress.collaboration_membrane import resolve_collaboration_context

        context = resolve_collaboration_context(
            details={"claim_label": "asserted", "reversible": True}
        )
        if not context.get("charter_present"):
            errors.append("collaboration charter not loadable")
        elif not context.get("admitted"):
            errors.append(
                "blocking invariants: " + ", ".join(context.get("blocking_invariants") or [])
            )

    if errors:
        for err in errors:
            print(f"[collaboration-charter-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_constitutional_substrate.py", "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        print("[collaboration-charter-gate] FAIL: pytest")
        return 1

    print("[collaboration-charter-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
