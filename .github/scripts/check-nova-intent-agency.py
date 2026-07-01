#!/usr/bin/env python3
"""Nova Intent agency proof gate — consult integration, conflicts, closure, session reset."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Nova Intent agency proof tests.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    python = sys.executable

    tests = [
        "tests/test_intent_core.py",
        "tests/test_intent_store.py",
        "tests/test_intent_agency_evidence.py",
    ]
    print("[intent-agency-proof] running agency proof tests")
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
        print("[intent-agency-proof] FAIL: pytest")
        return 1

    sys.path.insert(0, str(repo_root))
    from src.cog_runtime.intent_agency_evidence import run_agency_evidence_fixture

    fixture = run_agency_evidence_fixture(
        prior_intent={
            "active_commitments": [
                {"commitment": "Finish cross-machine proof", "status": "active", "claim_posture": "asserted"}
            ]
        },
        next_intent={
            "active_commitments": [
                {"commitment": "Finish cross-machine proof", "status": "active", "claim_posture": "asserted"},
                {"commitment": "Run narrative evidence fixture", "status": "active", "claim_posture": "asserted"},
            ],
            "unified_closure": {"unified": False, "layers": []},
            "continuity_claim_posture": "asserted",
        },
        prior_narrative={"active_story": "Exploring new runtimes"},
        next_narrative={"active_story": "Hardening narrative evidence"},
    )
    print("[intent-agency-proof] session-reset fixture:", json.dumps(fixture, indent=2))
    if not fixture.get("passed"):
        print("[intent-agency-proof] FAIL: agency fixture did not pass")
        return 1

    print("[intent-agency-proof] OK: consult integration, conflicts, closure, and session-reset fixture passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
