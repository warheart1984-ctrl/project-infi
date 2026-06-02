#!/usr/bin/env python3
"""Narrative Trust Pack mutation gate — verifies MP-NTP-001 golden path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.mutation_engine import MutationEngine

REQUIRED_PATHS = (
    _ROOT / "docs/_future/mutations/MP-NTP-001.md",
    _ROOT / "schemas/deltas/narrative_trust_pack_MP-NTP-001.json",
    _ROOT / "tests/test_narrative_trust_pack_mutation_MP_NTP_001.py",
    _ROOT / "docs/proof/storyforge/NARRATIVE_TRUST_PACK_MP-NTP-001_PROOF.md",
)


def main() -> int:
    missing = [path.relative_to(_ROOT) for path in REQUIRED_PATHS if not path.is_file()]
    if missing:
        for item in missing:
            print(f"[narrative-trust-pack-mutation-gate] FAIL: missing {item}")
        return 1

    engine = MutationEngine(_ROOT)
    result = engine.verify("narrative_trust_pack", "MP-NTP-001")
    if not result.passed:
        for failure in result.failures:
            print(f"[narrative-trust-pack-mutation-gate] FAIL: {failure}")
        return 1

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(REQUIRED_PATHS[2]), "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr or "").strip().splitlines()
        suffix = detail[-1] if detail else "mutation tests failed"
        print(f"[narrative-trust-pack-mutation-gate] FAIL: {suffix}")
        return 1

    print("[narrative-trust-pack-mutation-gate] PASS: MP-NTP-001 verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
