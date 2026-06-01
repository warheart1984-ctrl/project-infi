#!/usr/bin/env python3
"""Validate UGR governed LLM provider execution artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REQUIRED = [
    "src/ugr/governed_llm_executor.py",
    "docs/contracts/UGR_LLM_PROVIDER_EXECUTION_CONTRACT.md",
    "tests/test_ugr_governed_llm_executor.py",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings = [f"missing required file: {rel}" for rel in REQUIRED if not (root / rel).exists()]
    status = "pass" if not findings else "fail"
    print(f"ugr llm provider manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    return 1 if findings and args.mode == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
