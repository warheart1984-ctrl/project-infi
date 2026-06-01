#!/usr/bin/env python3
"""Nova Narrative continuity proof gate — persistence, rehydration, A/B."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Nova Narrative continuity proof tests.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    python = sys.executable

    tests = [
        "tests/test_narrative_runtime.py",
        "tests/test_narrative_store.py",
        "tests/test_narrative_continuity_proof.py",
    ]
    print("[narrative-proof] running continuity proof tests")
    completed = subprocess.run(
        [python, "-m", "pytest", *tests, "-q"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    print(completed.stdout)
    if completed.returncode != 0:
        print(completed.stderr)
        print("[narrative-proof] FAIL: pytest")
        return 1

    sys.path.insert(0, str(repo_root))
    from src.cog_runtime.narrative_continuity import compare_continuity_treatment_vs_baseline

    fixture = compare_continuity_treatment_vs_baseline(
        {
            "working_on": "Cross-machine proof",
            "last_growth": "Composed turns integrated into Jarvis",
            "active_story": "Helping forge Wolf Cog OS",
            "becoming": "improving long-term continuity",
            "open_threads": ["Unified memory path"],
        },
        arc={
            "goal": "Helping forge Wolf Cog OS",
            "root_goal": "Helping forge Wolf Cog OS",
            "open_threads": ["Cross-machine proof"],
        },
        planning={"next_action": "Keep primary focus on: cross-machine proof"},
    )
    print("[narrative-proof] A/B fixture:", json.dumps(fixture, indent=2))
    if not fixture.get("passed"):
        print("[narrative-proof] FAIL: narrative did not beat baseline on fixture")
        return 1

    print("[narrative-proof] OK: persistence, rehydration, and A/B fixture passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
