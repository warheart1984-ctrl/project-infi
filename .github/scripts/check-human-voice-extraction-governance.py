#!/usr/bin/env python3
"""Human Voice Extraction governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable

    print("[human-voice-extraction-gate] running unit tests")
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_human_voice_extraction.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return 1

    print("[human-voice-extraction-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
