#!/usr/bin/env python3
"""Brain layer runtime governance gate."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / "schemas" / "brain_proposal.v1.json",
        root / "src" / "brain_layer_runtime.py",
        root / "src" / "brain_session_store.py",
    ]
    for path in required:
        if not path.is_file():
            print(f"[brain-layer-gate] FAIL: missing {path.relative_to(root)}")
            return 1
    api = (root / "src" / "api.py").read_text(encoding="utf-8")
    if "/api/operator/brain/sessions" not in api:
        print("[brain-layer-gate] FAIL: missing brain API")
        return 1
    env = dict(os.environ)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_brain_proposal_validator.py",
            "tests/test_brain_layer_runtime.py",
            "tests/test_brain_session_store.py",
            "-q",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return 1
    print("[brain-layer-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
