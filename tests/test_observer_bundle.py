"""Verify observer-bundle reproduces BK-PKG-1 on a clean stdlib path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1] / "observer-bundle"
EXPECTED_HASH = "b1d4f5a5c9a5e7d8565617aadd6240213664bd624120ba31dce290fbeba53f52"


def test_observer_bundle_verify_script() -> None:
    result = subprocess.run(
        [sys.executable, "continuity_verify.py", "BK-PKG-1.json"],
        cwd=BUNDLE,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "status: verified" in result.stdout
    assert f"canonical_hash: {EXPECTED_HASH}" in result.stdout


def test_observer_bundle_reproduce_script() -> None:
    result = subprocess.run(
        [sys.executable, "bone_king_reproduce.py", "BK-PKG-1.json"],
        cwd=BUNDLE,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "result: verified" in result.stdout
    assert "canonical_hash_match: True" in result.stdout
