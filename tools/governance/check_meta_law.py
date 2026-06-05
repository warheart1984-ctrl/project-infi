#!/usr/bin/env python3
"""Meta Architect Lawbook constitutional gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

LAWBOOK = _ROOT / "lawbook" / "META_ARCHITECT_LAWBOOK.md"
SPEC = _ROOT / "docs" / "substrate" / "CONSTITUTIONAL_LAYER.md"
ENGINE = _ROOT / "src" / "substrate" / "meta_law_engine.py"


def main() -> int:
    errors: list[str] = []
    for path in (LAWBOOK, SPEC, ENGINE):
        if not path.is_file():
            errors.append(f"missing: {path.relative_to(_ROOT)}")

    if not errors:
        from src.substrate.meta_law_engine import resolve_constitutional_context

        context = resolve_constitutional_context()
        if not context.get("lawbook_present"):
            errors.append("constitutional lawbook not loadable")
        elif context.get("blocking_invariants"):
            errors.append(
                "blocking invariants: " + ", ".join(context["blocking_invariants"])
            )

    if errors:
        for err in errors:
            print(f"[meta-law-gate] FAIL: {err}")
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
        print("[meta-law-gate] FAIL: pytest")
        return 1

    print("[meta-law-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
