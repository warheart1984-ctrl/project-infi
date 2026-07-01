#!/usr/bin/env python3
"""AI Factory governance gate for CI."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AI Factory v1 build and tests.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--spec", default="factory/specs/nova-default.yaml")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    print("[ai-factory-gate] running factory unit tests")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_ai_factory.py", "-q"],
        cwd=str(repo_root),
        check=False,
    )
    if proc.returncode != 0:
        print("[ai-factory-gate] FAIL: unit tests")
        return proc.returncode

    if args.skip_build:
        print("[ai-factory-gate] OK: tests only (--skip-build)")
        return 0

    spec_path = repo_root / args.spec
    if not spec_path.is_file():
        print(f"[ai-factory-gate] FAIL: missing spec {spec_path}")
        return 1

    print("[ai-factory-gate] running full factory build with verification lanes")
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_factory",
            "build",
            "--spec",
            str(spec_path),
            "--repo-root",
            str(repo_root),
            "--output",
            "json",
        ],
        cwd=str(repo_root),
        check=False,
    )
    if build.returncode != 0:
        print("[ai-factory-gate] FAIL: factory build")
        return build.returncode

    print("[ai-factory-gate] OK: build + verification complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
