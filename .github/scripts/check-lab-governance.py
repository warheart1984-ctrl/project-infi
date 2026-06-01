#!/usr/bin/env python3
"""Lab Console governance gate for CI."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Lab Console v1 tests and optional init smoke.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--skip-init-smoke", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    print("[lab-gate] running lab unit tests")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_lab.py",
            "tests/test_lab_worktree.py",
            "-q",
        ],
        cwd=str(repo_root),
        check=False,
    )
    if proc.returncode != 0:
        print("[lab-gate] FAIL: unit tests")
        return proc.returncode

    if args.skip_init_smoke:
        print("[lab-gate] OK: tests only (--skip-init-smoke)")
        return 0

    fixture = repo_root / "lab" / "fixtures" / "sample-repo"
    if not fixture.is_dir():
        print("[lab-gate] SKIP: fixture repo missing")
        return 0

    print("[lab-gate] running init smoke on fixture repo (ephemeral runtime)")
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        runtime = Path(tmp) / "runtime"
        init = subprocess.run(
            [
                sys.executable,
                "-m",
                "lab",
                "init",
                "--project",
                "lab-gate-smoke",
                "--source",
                str(fixture),
                "--runtime-root",
                str(runtime),
                "--ledger-path",
                str(runtime / "lab_ledger.jsonl"),
            ],
            cwd=str(repo_root),
            check=False,
        )
        if init.returncode != 0:
            print("[lab-gate] FAIL: lab init smoke (ensure fixture is a git repo in CI setup)")
            return init.returncode

    print("[lab-gate] OK: tests complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
