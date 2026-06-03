#!/usr/bin/env python3
"""Release 29 integration + Story Forge execution bundle closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/INTEGRATION_UNIVERSAL_BUNDLE_V1_PROOF.md",
    _ROOT / "docs/proof/storyforge/STORYFORGE_EXECUTION_BUNDLE_V1_PROOF.md",
)
TESTS = (
    "tests/test_alt29_integration.py",
    "tests/test_story_forge_launcher_organ.py",
    "tests/test_media_processor_bridge_organ.py",
    "tests/test_operator_cognition_coherence_fabric.py::test_alt29_story_forge_execution_layers_at_v124",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt29-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *TESTS, "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return 1
    schema = _ROOT / "schemas/operator_cognition_coherence_fabric.v1.24.json"
    if not schema.is_file():
        print("[alt29-closure-gate] FAIL: missing coherence v1.24 schema")
        return 1
    print("[alt29-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
